# This builds the base images that we can use for development testing. See
#   .github/workflows/debug.yml
# It is also used in main GitHub Actions workflow: see .github/workflows/github.yml).
#
# Notes:
# - Mostly based initially on
#     https://stackoverflow.com/a/70866416 [How to install python specific version on docker?]
# - For Docker docs, see https://docs.docker.com/get-started.
# - The avoid linux continuation characters (i.e., \<newline), <<END-style heredocs are used: See
#      https://www.docker.com/blog/introduction-to-heredocs-in-dockerfiles
#   This allows for commenting out code (e.g., inline comment within heredoc group).
#
# Usage:
# 1. Build the image:
#   $ docker build -t mezcla-dev -f- . <Dockerfile
#   # TODO: build --platform linux/x86_64 ...
# 2. Run tests using the created image (n.b., uses entrypoint at end below with run_tests.bash):
#   $ docker run -it --rm --mount type=bind,source="$(pwd)",target=/home/mezcla mezcla-dev
#   TODO: --mount => --volume???
#   NOTE: --rm removes container afterwards; -it is for --interactive with --tty
# 3. [Optional] Run a bash shell using the created image:
#   $ docker run -it --rm --entrypoint='/bin/bash' --mount type=bind,source="$(pwd)",target=/home/mezcla mezcla-dev
# 4. Remove the image:
#   $ docker rmi mezcla-dev
#
# Warning:
# - *** Changes need to be synchronized in 3 places: Dockerfile, tools/local-workflow.sh, and .github/workflows/*.yml!
# - Python scripts should be invoked with python3 due to quirk with distribution archive
#   lacking plain python executable (unlike anaconda).
#
# TODO3: keep in synch with ~/bin version (https://github.com/tomasohara/shell-scripts)
#

## NOTE: Uses a smaller image to speed up build
## TEST: FROM ghcr.io/catthehacker/ubuntu:act-latest
## OLD: FROM catthehacker/ubuntu:act-20.04
ARG UBUNTU_VERSION="22.04"
FROM catthehacker/ubuntu:act-${UBUNTU_VERSION}

ARG WORKDIR=/home/mezcla
ARG REQUIREMENTS=$WORKDIR/requirements.txt

## TODO?: RUN mkdir -p $WORKDIR

WORKDIR $WORKDIR

# Set the Python version to install
# Note: The workflow uses versions 3.9 to 3.11 for installations under runner VM
#
# To find URL links, see https://github.com/actions/python-versions:
# ex: https://github.com/actions/python-versions/releases/tag/3.11.4-5199054971
#
## OLD: ARG PYTHON_VERSION=3.8.12
## TODO:
ARG PYTHON_VERSION=3.11.4
## TODO: ARG PYTHON_VERSION=""
## OLD: ARG PYTHON_TAG="117929"
## TODO:
ARG PYTHON_TAG="5199054971"

# Set default debug level (n.b., use docker build --build-arg "arg1=v1" to override)
# Also optionally set the regex of tests to run.
# Note: maldito act/nektos/docker not overriding properly
## TODO2: fixme (see tools/run_tests.bash for workaround).
## TODO: ARG DEBUG_LEVEL=2
ARG DEBUG_LEVEL=4
## DEBUG: ARG DEBUG_LEVEL=5
ARG TEST_REGEX=""
## DEBUG: ARG TEST_REGEX="simple_main_example"

# Show initial disk usage
# See https://github.com/orgs/community/discussions/25678 [No space left on device]
#
RUN <<END_RUN
    df --human-readable
    ## TODO: track down stupid problem with step failing
    ## echo "Top directories by disk usage (pre-install):";
    ## du --block-size=1K / 2>&1 | sort -rn | head -20;
    true;                               # ensure success (quirk w/ head)
END_RUN

# Temp: remove unneeded software taking up much disk space (e.g., node)
RUN <<END_RUN
    echo "Warning: removing unneeded software"
    /bin/rm -rf /opt/acttoolcache/node
    df -h /
END_RUN

# Install Python
# See https://stackoverflow.com/a/70866416 [How to install python specific version on docker?]
#
# Download, extract, and install the specified Python version
# Note:
# - Uses versions prepared for Github Actions
# - To find URL links, see https://github.com/actions/python-versions:
#   ex: https://github.com/actions/python-versions/releases/tag/3.11.4-5199054971
# - Also see https://stackoverflow.com/questions/74673048/github-actions-setup-python-stopped-working.
# - The wget -qO option is for quiet output to a file.
# - TODO3: report error if download fails
RUN if [ "$PYTHON_VERSION" != "" ]; then                                                 \
        wget -qO /tmp/python-${PYTHON_VERSION}-linux-${UBUNTU_VERSION}-x64.tar.gz "https://github.com/actions/python-versions/releases/download/${PYTHON_VERSION}-${PYTHON_TAG}/python-${PYTHON_VERSION}-linux-${UBUNTU_VERSION}-x64.tar.gz" &&     \
        mkdir -p /opt/hostedtoolcache/Python/${PYTHON_VERSION}/x64 &&                    \
        tar -xzf /tmp/python-${PYTHON_VERSION}-linux-${UBUNTU_VERSION}-x64.tar.gz                    \
            -C /opt/hostedtoolcache/Python/${PYTHON_VERSION}/x64 --strip-components=1 && \
        rm /tmp/python-${PYTHON_VERSION}-linux-${UBUNTU_VERSION}-x64.tar.gz;                          \
    fi

## TODO (use streamlined python installation):
## RUN apt-get update && \
##     apt-get install -y software-properties-common && \
##     add-apt-repository -y ppa:deadsnakes/ppa && \
##     apt-get update && \
##     apt-get install -y python$PYTHON_MAJ_MIN

# Some programs require a "python" binary
## OLD: RUN ln -s $(which python3) /usr/local/bin/python

# Set the working directory visible
# Make sure the installed python takes precedence (TODO: use var to reduce redundancy with above)
ENV PYTHONPATH="${PYTHONPATH}:$WORKDIR"
ENV PATH="/opt/hostedtoolcache/Python/${PYTHON_VERSION}/x64/bin:${PATH}:$WORKDIR"

# Install pip for the specified Python version (TODO rm)
RUN if [ "$PYTHON_VERSION" == "" ]; then                                                \
        wget -qO /tmp/get-pip.py "https://bootstrap.pypa.io/get-pip.py" &&              \
        python3 /tmp/get-pip.py;                                                        \
        true || rm /tmp/get-pip.py;                                                     \
    fi

# Copy the project's requirements file to the container
COPY ./requirements.txt $REQUIREMENTS

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && apt-get clean

# Install the package requirements
# NOTE: The workflow only handles requirements for the runner VM, not the docker container;
# Also, the results aren't cached to save space in the image.
RUN <<END_RUN
  ## OLD
  ## if [ "$(which nltk)" == "" ]; then
  ##      python3 -m pip install --verbose --no-cache-dir --requirement $REQUIREMENTS;
  ##      ## TODO?
  ##      ## # note: makes a second pass for failed installations, doing non-binary
  ##      ## python3 -m pip install --verbose --no-cache-dir --ignore-installed --no-binary --requirement $REQUIREMENTS;
  ## fi
  python3 -m pip install --verbose --no-cache-dir --requirement $REQUIREMENTS;
END_RUN
## TODO3: add option for optional requirements (likewise, for all via '#full#")
##   RUN python3 -m pip install --verbose $(perl -pe 's/^#opt#\s*//g;' $REQUIREMENTS | grep -v '^#')

## TEMP workaround: copy source to image
## COPY . $WORKDIR/mezcla

# Download the NLTK required data
RUN python3 -m nltk.downloader -d /usr/local/share/nltk_data punkt punkt_tab averaged_perceptron_tagger averaged_perceptron_tagger_eng stopwords

# Install required tools and libraries (TODO: why lsb-release?)
# Note: cleans the apt-get cache
RUN apt-get update -y && apt-get install --yes lsb-release && apt-get clean all
# note: rcs needed for merge (TODO: place in required-packages.txt)
RUN apt-get install --yes enchant-2 rcs

# Show disk usage and other info when debugging
RUN <<END_RUN
    df --human-readable
    ## TODO: track down stupid problem with step failing
    ## echo "Top directories by disk usage (post-install):";
    ## du --block-size=1K / 2>&1 | sort -rn | head -20;
    #
    which python3
    python3 --version
    #
    true;                               # ensure success (quirk w/ head)
END_RUN

# Run the test, normally pytest over mezcla/tests
# Note: the status code (i.e., $?) determines whether docker run succeeds (e.g., OK if 0)
ENTRYPOINT DEBUG_LEVEL=$DEBUG_LEVEL TEST_REGEX="$TEST_REGEX" './tools/run_tests.bash'
