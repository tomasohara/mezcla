#! /usr/bin/env/bash

# This script uses GitHub local actions via act:
#   https://github.com/nektos/act
# It builds a Docker image and runs a Github Actions workflow locally.
#
# Note:
# - This should be synchronized with the shell-scripts repo:
#   https://github.com/tomasohara/shell-scripts
# - When running under a Mac M1 the architecture needs to be specified to x64_64 (amd).
#   This is a no-op otherwise (e.g., under Linux) as x64_64 is used by defauly.
# - Disables following shellcheck warnings
#   SC2086: Double quote to prevent globbing)
#

# trace-vars(var, ...): trace each VAR in command line
# note: output format: VAR1=VAL1; ... VARn=VALn;
function trace-vars {
    local var
    for var in "$@"; do
        echo -n "$var=$(eval echo "\${$var}"); "
    done
    echo
}

# Variables
# note:
# - USER_ENV is of form "ENV1=val1 ENV2=val2 ...".
# - act pull is not required (n.b., misleading error message due to permissions, etc.).
IMAGE_NAME="local/test-act:latest"
## BAD: ACT_WORKFLOW="ubuntu-latest=local/test-act"
ACT_PULL="false"
DEBUG_LEVEL="${DEBUG_LEVEL:-2}"
USER_ENV="${USER_ENV:-}"
RUN_DOCKER="${RUN_DOCKER:-0}"
RUN_WORKFLOW="${RUN_WORKFLOW:-1}"
# TODO3: put all env. init up here for clarity
#   RUN_BUILD, RUN_WORKFLOW, WORKFLOW_FILE
#
# Trace out main environment overrides
if [ "$DEBUG_LEVEL" -ge 4 ]; then
    echo "in $0 $*"
    trace-vars IMAGE_NAME ACT_PULL LOCAL_REPO_DIR DEBUG_LEVEL GIT_BRANCH USER_ENV
fi

# Set bash regular and/or verbose tracing
if [ "${TRACE:-0}" = "1" ]; then
    set -o xtrace
fi
if [ "${VERBOSE:-0}" = "1" ]; then
    set -o verbose
fi

# Do sanity checks for potential problems
## TODO1: fix bug with image selection blocking progress (set default and disable interactive mode)
##   choose the default image you want to use with act
if [[ ("$RUN_WORKFLOW" == "1") && (! -e ~/.actrc) ]]; then
    echo "Error: run act to configure default image in ~/.actrc"
    exit
fi
if [[ ("$RUN_DOCKER" == "1") && ("" == "$(groups | grep docker)") ]]; then
    echo "Error: you need to be in the docker group to use act (or docker)"
    exit
fi

# Build the Docker image
if [ "${RUN_BUILD:-0}" = "1" ]; then
    echo "Building Docker image: $IMAGE_NAME"
    docker build --platform linux/x86_64 -t "$IMAGE_NAME" .
fi

# Run the Github Actions workflow locally
if [[ "$RUN_WORKFLOW" == "1" ]]; then
    file="${WORKFLOW_FILE:-act.yml}"
    echo "Running Github Actions locally w/ $file"
    ## TODO2: get act environment support working
    # Note: Unfortunately, the environment setting is not affecting the docker
    # invocation. A workaround is to modify the 'Run tests' steps in the
    # workflow configuration file (e.g., .github/workflows/debug.yml).
    act="${ACT_PROGRAM:-act}"
    misc_args=()
    # note: ACT_JSON can be used to disable act-specific flags (e.g., to enable runner matrix)
    json="${ACT_JSON:-""}"
    if [ "$json" != "" ]; then misc_args+=(--eventpath ./.github/workflows/"$json"); fi;
    "$act" --verbose --env "DEBUG_LEVEL=$DEBUG_LEVEL $USER_ENV" --container-architecture linux/amd64 --pull="$ACT_PULL" --workflows ./.github/workflows/"$file"  "${misc_args[@]}"
fi

# Run via docker directly
if [ "$RUN_DOCKER" = "1" ]; then
    echo "Running Tests via Docker"
    # Convert VAR1=val1 VAR2=val2 ... to "--env VAR1=val1 --env VAR2=val2 ..."
    user_env_spec=$(echo " $USER_ENV" | perl -pe 's/ (\w+=)/ --env $1/g;')
    # shellcheck disable=SC2086
    docker run -it --env DEBUG_LEVEL="$DEBUG_LEVEL" $user_env_spec --mount type=bind,source="$(pwd)",target=/home/mezcla mezcla-dev
fi
