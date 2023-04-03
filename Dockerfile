# This builds the base images that we can use for development
#
# Build the image:
# $ docker build -t mezcla-dev -f- . <Dockerfile
#
# Run the image:
# $ docker run -it --rm  --mount type=bind,source="$(pwd)",target=/home/mezcla mezcla-dev
#

FROM python:3.8.16

ARG WORKDIR=/home/mezcla
ARG REQUIREMENTS=$WORKDIR/requirements.txt

WORKDIR $WORKDIR

RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y build-essential

# Set the environment variables
ENV PYTHONPATH="${PYTHONPATH}:$WORKDIR"

# Install the requirements
RUN python -m pip install --upgrade pip
COPY ./requirements.txt $REQUIREMENTS
RUN python -m pip install -r $REQUIREMENTS
RUN python -m pip install --verbose $(perl -00 -pe 's/^#opt#\s*//gm;' $REQUIREMENTS | grep -v '^#')

CMD ["/bin/bash"]