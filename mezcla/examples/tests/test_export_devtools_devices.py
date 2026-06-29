#! /usr/bin/env python3
#
# Test(s) for ../export_devtools_devices.py
#
# - This can be run as follows (e.g., from root of repo):
#   $ pytest mezcla/examples/tests/test_<module>.py
#
# notes:
# - By Gemini 3.
# - global filter
#   pylint: disable=protected-access
#
#--------------------------------------------------------------------------------
# Sample 

"""Tests for export_devtools_devices module"""

# Installed modules
import pytest

# Local modules
from mezcla import debug
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla.tests.common_module import fix_indent

# Note: Two references are used for the module to be tested:
#    THE_MODULE:               module object (e.g., <module 'mezcla.main' ...>)
#    TestIt.script_module:     dotted module path (e.g., "mezcla.main")
THE_MODULE = None
try:
    import export_devtools_devices as THE_MODULE
except:
    system.print_exception_info("export_devtools_devices import") 

NOKIA_N9_INPUT = """

    const emulatedDevices = [
        // DEVICE-LIST-BEGIN
        {
        'show-by-default': false,
        'title': 'Nokia N9',
        'screen': {
          'horizontal': {'width': 854, 'height': 480},
          'device-pixel-ratio': 1,
          'vertical': {'width': 480, 'height': 854},
        },
        'capabilities': ['touch', 'mobile'],
        'user-agent':
            'Mozilla/5.0 (MeeGo; NokiaN9) AppleWebKit/534.13 (KHTML, like Gecko) NokiaBrowser/8.5.0 Mobile Safari/534.13',
        'type': 'phone',
        }
      // DEVICE-LIST-END
];
"""

NOKIA_N9_OUTPUT = """
    title,width,height,device-pixel-ratio,user-agent
    Nokia N9,480,854,1,"Mozilla/5.0 (MeeGo; NokiaN9) AppleWebKit/534.13 (KHTML, like Gecko) NokiaBrowser/8.5.0 Mobile Safari/534.13"
"""
    
class TestIt(TestWrapper):
    """Test suite for export_devtools_devices.py"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_00_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")
        temp_file = self.create_temp_file(NOKIA_N9_INPUT)
        output = self.run_script(data_file=temp_file)
        ## TODO? self.do_assert(output.strip() == fix_indent(NOKIA_N9_OUTPUT.strip()))
        assert (output.strip() == fix_indent(NOKIA_N9_OUTPUT).strip())
        return

    def test_01_extract_device_block(self):
        """Test the extraction of DEVICE-LIST block."""
        helper = THE_MODULE.Helper()
        text = "// DEVICE-LIST-BEGIN\nsome content\n// DEVICE-LIST-END"
        result = helper._extract_device_block(text)
        self.do_assert("some content" in result)

    def test_02_extract_field(self):
        """Test extraction of specific fields."""
        helper = THE_MODULE.Helper()
        text = "'width': 375,"
        result = helper._extract_field(r"'width':\s*([0-9.]+)", text)
        self.do_assert(result == "375")
        
        # Test missing field returns default
        result_missing = helper._extract_field(r"'height':\s*([0-9.]+)", text, default="missing")
        self.do_assert(result_missing == "missing")

        # Test implicit match option with optional parts
        text_optional = "'title': i18nLazyString('iPhone SE')"
        result_opt = helper._extract_field(r"'title':\s*(?:i18nLazyString\([^)]*\)|'([^']*)')", text_optional, default="missing")
        self.do_assert(result_opt == "missing") # outer matched but inner capture is empty so we expect default

    def test_03_process(self):
        """Test full process method output."""
        helper = THE_MODULE.Helper()
        text = '''// DEVICE-LIST-BEGIN
  {
    'title': 'Test Phone',
    'screen': {
      'device-pixel-ratio': 2,
      'vertical': {
        'width': 300,
        'height': 600,
      },
    },
    'user-agent': 'Test Agent',
  },
// DEVICE-LIST-END
'''
        result = helper.process(text)
        self.do_assert(result is True)
        stdout = self.get_stdout()
        self.do_assert("title,width,height,device-pixel-ratio,user-agent" in stdout)
        self.do_assert('Test Phone,300,600,2,"Test Agent"' in stdout)


#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
