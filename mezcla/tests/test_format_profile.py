#! /usr/bin/env python
#
# Tests for format_profile module
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_train_language_model.py
#

"""Tests for format_profile module"""

# Standard packages
import re

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper

class TestFormatProfile(TestWrapper):
    """Class for testcase definition"""
    None

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])