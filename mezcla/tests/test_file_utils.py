#! /usr/bin/env python
#
# Test(s) for ../file_utils.py
#


"""Tests for file_utils module"""


# Standard packages
import unittest


# Local packages
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug
from mezcla import glue_helpers as gh


# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module   string name
import mezcla.file_utils as file_utils


class TestIt(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.derive_tested_module_name(__file__)
    # TODO: use_temp_base_dir = True            # treat TEMP_BASE as directory
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)


    ## TODO: optional setup methods
    ##
    ## @classmethod
    ## def setUpClass(cls):
    ##     """One-time initialization (i.e., for entire class)"""
    ##     debug.trace(6, f"TestIt.setUpClass(); cls={cls}")
    ##     # note: should do parent processing first
    ##     super().setUpClass()
    ##     ...
    ##     return
    ##
    ## def setUp(self):
    ##     """Per-test setup"""
    ##     debug.trace(6, f"TestIt.setUp(); self={self}")
    ##     # note: must do parent processing first (e.g., for temp file support)
    ##     super().setUp()
    ##     ...
    ##     return


    def test_get_directory_listing(self):
        """
        Tests for get_directory_listing(path          = '.',
                                        recursive     = False,
                                        long          = False,
                                        readable_size = False,
                                        return_string = True,
                                        make_unicode  = False)
        """
        # WORK-IN-PROGRESS


    def test_get_information(self):
        """Tests for def get_information(path,
                                         readable_size = False,
                                         return_string = False)
        """
        ## WORK-IN-PROGRESS


    def test_get_permissions(self):
        """Tests for get_permissions(path)"""
        test_file = '/tmp/gp_test.cpp'
        gh.run(f'touch {test_file}')
        ls_permissions = gh.run(f'ls -l {test_file}')[:10]
        self.assertEqual(file_utils.get_permissions(test_file), ls_permissions)


    def test_get_modification_date(self):
        """Tests for get_modification_date(path)"""
        test_file = '/tmp/gp_test.cpp'
        gh.run(f'touch {test_file}')
        ls_date = gh.run(f'ls -l {test_file}')[39:51]
        self.assertEqual(file_utils.get_modification_date(test_file, strftime='%b %-d %-H:%-M'), ls_date)


    ## TODO: optional cleanup methods
    ##
    ## def tearDown(self):
    ##     debug.trace(6, f"TestIt.tearDown(); self={self}")
    ##     super(TestIt, cls).tearDownClass()
    ##     ...
    ##     return
    ##
    ## @classmethod
    ## def tearDownClass(cls):
    ##     debug.trace(6, f"TestIt.tearDownClass(); cls={cls}")
    ##     super(TestIt, self).tearDown()
    ##     ...
    ##     return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    unittest.main()
