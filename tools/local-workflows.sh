#!/bin/bash

# This script builds a Docker image and runs a Github Actions workflow locally.
#
# Note:
# - When running under a Mac M1 the architecture needs to be specified to x64_64 (amd).
#   This is a no-op otherwise (e.g., under Linux) as x64_64 is used by defauly.
#

# Variables
IMAGE_NAME="local/test-act:latest"
ACT_WORKFLOW="ubuntu-latest=local/test-act"
ACT_PULL="false"

# Build the Docker image
echo "Building Docker image: $IMAGE_NAME"
docker build --platform linux/x86_64 -t "$IMAGE_NAME" .

# Run the Github Actions workflow locally
echo "Running Github Actions locally"
act --container-architecture linux/amd64 --pull="$ACT_PULL" -P "$ACT_WORKFLOW" -W ./.github/workflows/act.yml
