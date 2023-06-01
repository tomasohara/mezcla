# This builds the base images that we can use for development
#
# Notes:
#   - Docker docs https://docs.docker.com/get-started/
#
# Build the image:
#   $ docker build -t mezcla-dev -f- . <Dockerfile
# Run tests using the created image (n.b., uses entrypoint at end below with run_tests.bash):
#   $ docker run -it --rm --mount type=bind,source="$(pwd)",target=/home/mezcla mezcla-dev
# Run a bash shell using the created image:
#   $ docker run -it --rm --entrypoint='/bin/bash' --mount type=bind,source="$(pwd)",target=/home/mezcla mezcla-dev
# Remove the image:
#   $ docker rmi mezcla-dev
#

FROM ubuntu:18.04

ARG WORKDIR=/home/mezcla
ARG REQUIREMENTS=$WORKDIR/requirements.txt

## TODO?: RUN mkdir -p $WORKDIR

WORKDIR $WORKDIR

# Install Python
# https://stackoverflow.com/a/70866416
#
# Note: we install Python 3.8 to maintain compatibility with some libraries
# Note: DEBIAN_FRONTEND=noninteractive must be setted on-the-fly to avoid unintended changes
RUN apt update -y && apt-get install sudo -y
RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo
RUN sudo apt upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y wget build-essential checkinstall  libreadline-gplv2-dev  libncursesw5-dev  libssl-dev  libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev && \
    cd /usr/src && \
    sudo wget https://www.python.org/ftp/python/3.8.10/Python-3.8.10.tgz && \
    sudo tar xzf Python-3.8.10.tgz && \
    cd Python-3.8.10 && \
    DEBIAN_FRONTEND=noninteractive sudo ./configure --enable-optimizations && \
    DEBIAN_FRONTEND=noninteractive sudo make install
RUN apt-get update -y && apt-get install git -y

# Some programs require a "python" binary
RUN ln -s $(which python3) /usr/local/bin/python

# Set the working directory visible
ENV PYTHONPATH="${PYTHONPATH}:$WORKDIR"

# Install the package requirements
RUN python -m pip install --upgrade pip
COPY ./requirements.txt $REQUIREMENTS
RUN python -m pip install -r $REQUIREMENTS
RUN python -m pip install --verbose $(perl -pe 's/^#opt#\s*//g;' $REQUIREMENTS | grep -v '^#')

# Download the NLTK required data
## OLD: RUN python -m nltk.downloader -d /usr/local/share/nltk_data all
RUN python -m nltk.downloader -d /usr/local/share/nltk_data punkt averaged_perceptron_tagger

# Install required tools and libraries
RUN apt-get update -y && apt-get install -y lsb-release && apt-get clean all
RUN apt install rcs

# Run the test, normally pytest over mezcla/tests
# Note: the status code (i.e., $?) determines whether docker run succeeds (e.h., OK if 0)
ENTRYPOINT './tools/run_tests.bash'
