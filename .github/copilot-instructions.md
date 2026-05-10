# Copilot Instructions for Mezcla

This repository contains miscellaneous Python scripts and utilities for R&D.

See AGENTS.md in project root for more general instructions.

## Build, Test, and Lint Commands

### Testing
The primary test runner is a Bash script that wraps `pytest` and a custom test runner.
Normally, you only need to run tests for modules that you change; however, if the
changes are to core modules like main.py or system.py, it is best to rerun 
all tests.

*   **Run specific tests**:
    Use the `TEST_REGEX` environment variable to filter tests by name.
    ```bash
    TEST_REGEX='audio' ./run_tests.bash
    ```

*   **Run all tests**:
    ```bash
    ./run_tests.bash
    ```

*   **Environment Variables**:
    *   `DEBUG_LEVEL`: Integer (0-6) for verbosity.
    *   `TRACE`: Set to `1` for `set -o xtrace`.
    *   `DRY_RUN`: Set to `1` to show commands without executing.
    *   `INVOKE_PYTEST_DIRECTLY`: Set to `1` to bypass the custom wrapper.

### Documentation
Documentation is built with Sphinx.
*   **Build HTML docs**:
    ```bash
    cd docs && make html
    ```

### Packaging
*   Legacy setup: `setup.py`
*   Modern setup: `pyproject.toml` (uses Poetry/Flit hybrid approach).

## High-Level Architecture

*   **`mezcla/`**: The main package containing utility modules.
    *   Modules range from text processing (`text_utils.py`, `tfidf/`) to audio (`audio.py`) and ML (`keras_param_search.py`).
*   **`mezcla/tests/`**: Unit tests for the package.
*   **`mezcla/examples/`**: Example usage scripts.
*   **`tools/`**: Helper scripts for maintenance and testing (e.g., `run_tests.bash`).

