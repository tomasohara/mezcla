#! /usr/bin/env python
#
# Test(s) for glue_helpers.py. This can be run as follows:
# $ PYTHONPATH="." tests/test_glue_helpers.py
#
# TODO:
# - Add support for write_lines & read_lines.
# - Add support for other commonly used functions.
#

"""Tests for glue_helpers module"""

import os
import unittest

import tomas_misc.glue_helpers as gh
import tomas_misc.tpo_common as tpo


class TestIt(unittest.TestCase):
    """Class for testcase definition"""

    def setUp(self):
        """Per-test initializations, including disabling tracing of scripts invoked via run()"""
        tpo.debug_print("setUp()", 4)
        gh.disable_subcommand_tracing()
        return

    def test_extract_matches(self):
        """Tests for extract_matches(pattern, lines)"""
        ## OLD
        ## self.assertEqual(gh.extract_matches("Mr. (\S+)", ["Mr. Smith", "Mr. Jones", "Mr.X"]), ["Smith", "Jones"])
        ## self.assertNotEqual(gh.extract_matches("\t\S+", ["abc\tdef", "123\t456"]), ["def", "456"])
        self.assertEqual(gh.extract_matches(r"Mr. (\S+)", ["Mr. Smith", "Mr. Jones", "Mr.X"]), ["Smith", "Jones"])
        self.assertNotEqual(gh.extract_matches(r"\t\S+", ["abc\tdef", "123\t456"]), ["def", "456"])
        return

    def test_basename(self):
        """Tests for basename(path, extension)"""
        self.assertEqual(gh.basename("fubar.py", ".py"), "fubar")
        self.assertNotEqual(gh.basename("fubar.py", ""), "fubar")
        return

    def test_resolve_path(self):
        """Tests for resolve_path(filename)"""
        script = "glue_helpers.py"
        test_script = "test_glue_helpers.py"
        # The main script should resolve to parent directory but this one to test dir
        self.assertNotEqual(gh.resolve_path(script), 
                            os.path.join(os.path.dirname(__file__), test_script))
        self.assertEqual(gh.resolve_path(test_script), 
                         os.path.join(os.path.dirname(__file__), test_script))
        return


if __name__ == '__main__':
    unittest.main()
