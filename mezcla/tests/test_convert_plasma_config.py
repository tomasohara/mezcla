#! /usr/bin/env python3
#
# Test(s) for ../convert_plasma_config.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_convert_plasma_config.py
#

"""Tests for convert_plasma_config module"""

# Standard modules
import os

# Installed modules
import pytest

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests

# Note: Two references are used for the module to be tested:
#    THE_MODULE:               module object
#    TestIt.script_module:     dotted module path
THE_MODULE = None
try:
    import mezcla.convert_plasma_config as THE_MODULE
except:
    system.print_exception_info("convert_plasma_config import")

# Note: sanity test for customization
if not my_re.search(r"\btemplate.py$", __file__):
    debug.assertion("mezcla.*template" not in str(THE_MODULE))

# Sample data: minimal panel with a task manager applet
SAMPLE_MINIMAL = """\
[ActionPlugins][0]
RightButton;NoModifier=org.kde.contextmenu

[Containments][3]
activityId=
formfactor=2
immutability=1
lastScreen=0
location=4
plugin=org.kde.panel
wallpaperplugin=org.kde.image

[Containments][3][Applets][27]
immutability=1
plugin=org.kde.plasma.taskmanager

[Containments][3][Applets][27][Configuration]
PreloadWeight=18

[Containments][3][Applets][27][Configuration][General]
groupedTaskVisualization=3
onlyGroupWhenFull=false
showToolTips=false
wheelEnabled=false

[Containments][3][Applets][4]
immutability=1
plugin=org.kde.plasma.kickoff

[Containments][3][Applets][4][Configuration]
PreloadWeight=100

[Containments][3][Applets][4][Configuration][Shortcuts]
global=Alt+F1

[Containments][3][General]
AppletOrder=4;27

[ScreenMapping]
itemsOnDisabledScreens=
"""

# Sample with systray cross-reference
SAMPLE_SYSTRAY = """\
[Containments][3]
formfactor=2
lastScreen=0
location=4
plugin=org.kde.panel

[Containments][3][Applets][8]
immutability=1
plugin=org.kde.plasma.systemtray

[Containments][3][Applets][8][Configuration]
PreloadWeight=88
SystrayContainmentId=9

[Containments][3][General]
AppletOrder=8

[Containments][9]
formfactor=2
lastScreen=0
location=4
plugin=org.kde.plasma.private.systemtray

[Containments][9][Applets][10]
immutability=1
plugin=org.kde.plasma.volume

[Containments][9][Applets][10][Configuration][General]
migrated=true
"""

# Sample with malformed section header
SAMPLE_MALFORMED = """\
[Containments][3]
formfactor=2
lastScreen=0
location=4
plugin=org.kde.panel

[Containments3Appletsts][31][Configuration][General]
groupedTaskVisualization=3
launchers=applications:systemsettings.desktop
"""

# Sample desktop folder containment
SAMPLE_DESKTOP = """\
[Containments][1]
activityId=cad4c661-475d-47d1-a689-8db7f67f6208
formfactor=0
immutability=1
lastScreen=0
location=0
plugin=org.kde.plasma.folder
wallpaperplugin=org.kde.image

[Containments][1][General]
ToolBoxButtonState=topcenter
ToolBoxButtonX=444
"""

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def test_01_data_file(self):
        """Tests run_script with minimal sample data"""
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")
        temp_file = self.create_temp_file(SAMPLE_MINIMAL)
        output = self.run_script(data_file=temp_file)
        self.do_assert(my_re.search(r"\[Container: Panel", output))
        self.do_assert(my_re.search(r"\[Container: Taskmanager", output))
        self.do_assert(my_re.search(r"sub-container: Kickoff", output))
        self.do_assert(my_re.search(r"sub-container: Taskmanager", output))
        return

    def test_02_simplify_plugin_name(self):
        """Test plugin name simplification"""
        debug.trace(4, f"TestIt.test_02_simplify_plugin_name(); self={self}")
        self.do_assert(THE_MODULE.simplify_plugin_name("org.kde.plasma.taskmanager") == "Taskmanager")
        self.do_assert(THE_MODULE.simplify_plugin_name("org.kde.plasma.private.systemtray") == "Systemtray")
        self.do_assert(THE_MODULE.simplify_plugin_name("org.kde.panel") == "Panel")
        self.do_assert(THE_MODULE.simplify_plugin_name("org.kde.plasma.digitalclock") == "Digitalclock")
        self.do_assert(THE_MODULE.simplify_plugin_name("touchpad") == "Touchpad")
        self.do_assert(THE_MODULE.simplify_plugin_name("org.kde.plasma.manage-inputmethod") == "ManageInputmethod")
        return

    def test_03_parse_section_header(self):
        """Test INI section header parsing"""
        debug.trace(4, f"TestIt.test_03_parse_section_header(); self={self}")
        result = THE_MODULE.parse_section_header("[Containments][35][Applets][55][Configuration][General]")
        self.do_assert(result == ["Containments", "35", "Applets", "55", "Configuration", "General"])
        result2 = THE_MODULE.parse_section_header("[ActionPlugins][0]")
        self.do_assert(result2 == ["ActionPlugins", "0"])
        return

    def test_04_converter_basic(self):
        """Test basic converter flow with minimal input"""
        debug.trace(4, f"TestIt.test_04_converter_basic(); self={self}")
        converter = THE_MODULE.PlasmaConfigConverter()
        converter.parse(SAMPLE_MINIMAL)
        converter.build_model()
        output = converter.convert()
        # Panel container should be present
        self.do_assert("[Container: Panel (screen:0, location:bottom)]" in output)
        # Task manager config should be flattened
        self.do_assert("groupedTaskVisualization=3" in output)
        self.do_assert("onlyGroupWhenFull=false" in output)
        self.do_assert("wheelEnabled=false" in output)
        # AppletOrder should be preserved
        self.do_assert("AppletOrder=4;27" in output)
        # ActionPlugins should pass through
        self.do_assert("[ActionPlugins][0]" in output)
        # ScreenMapping should pass through
        self.do_assert("[ScreenMapping]" in output)
        return

    def test_05_sub_containers(self):
        """Test sub-container declarations follow AppletOrder"""
        debug.trace(4, f"TestIt.test_05_sub_containers(); self={self}")
        converter = THE_MODULE.PlasmaConfigConverter()
        converter.parse(SAMPLE_MINIMAL)
        converter.build_model()
        output = converter.convert()
        # sub-containers should appear in AppletOrder sequence (4=kickoff, 27=taskmanager)
        kickoff_pos = output.index("sub-container: Kickoff")
        taskmanager_pos = output.index("sub-container: Taskmanager")
        self.do_assert(kickoff_pos < taskmanager_pos,
                       "Kickoff should appear before Taskmanager per AppletOrder")
        return

    def test_06_systray_crossref(self):
        """Test SystrayContainmentId is converted to systray-ref"""
        debug.trace(4, f"TestIt.test_06_systray_crossref(); self={self}")
        converter = THE_MODULE.PlasmaConfigConverter()
        converter.parse(SAMPLE_SYSTRAY)
        converter.build_model()
        output = converter.convert()
        self.do_assert("systray-ref:" in output)
        # SystrayContainmentId should NOT appear as raw key
        self.do_assert("SystrayContainmentId=" not in output)
        # Systray child applets should be listed
        self.do_assert("sub-container: Volume" in output)
        return

    def test_07_malformed_section_warning(self):
        """Test that malformed sections are detected and excluded"""
        debug.trace(4, f"TestIt.test_07_malformed_section_warning(); self={self}")
        converter = THE_MODULE.PlasmaConfigConverter()
        converter.parse(SAMPLE_MALFORMED)
        converter.build_model()
        output = converter.convert()
        # Malformed section content should NOT appear in output
        self.do_assert("Containments3Appletsts" not in output)
        # Properties from malformed section should be tracked as skipped
        self.do_assert(len(converter.skipped_properties) > 0,
                       "Expected skipped properties from malformed section")
        # All properties should still be accounted for
        unaccounted = len(converter.original_properties) - len(converter.accounted_indices)
        self.do_assert(unaccounted == 0,
                       f"Expected 0 unaccounted properties, got {unaccounted}")
        return

    def test_08_fidelity_validation(self):
        """Test that all input properties are accounted for"""
        debug.trace(4, f"TestIt.test_08_fidelity_validation(); self={self}")
        converter = THE_MODULE.PlasmaConfigConverter()
        converter.parse(SAMPLE_MINIMAL)
        converter.build_model()
        _output = converter.convert()
        converter.validate_fidelity()
        # All properties should be accounted for
        unaccounted = len(converter.original_properties) - len(converter.accounted_indices)
        self.do_assert(unaccounted == 0,
                       f"Expected 0 unaccounted properties, got {unaccounted}")
        return

    def test_09_desktop_folder(self):
        """Test desktop folder containment conversion"""
        debug.trace(4, f"TestIt.test_09_desktop_folder(); self={self}")
        converter = THE_MODULE.PlasmaConfigConverter()
        converter.parse(SAMPLE_DESKTOP)
        converter.build_model()
        output = converter.convert()
        self.do_assert("[Container: Folder (screen:0, activity:cad4c661)]" in output)
        self.do_assert("ToolBoxButtonState=topcenter" in output)
        self.do_assert("ToolBoxButtonX=444" in output)
        return

    def test_10_shortcuts_output(self):
        """Test that keyboard shortcuts are preserved in output"""
        debug.trace(4, f"TestIt.test_10_shortcuts_output(); self={self}")
        converter = THE_MODULE.PlasmaConfigConverter()
        converter.parse(SAMPLE_MINIMAL)
        converter.build_model()
        output = converter.convert()
        self.do_assert("[Shortcuts].global=Alt+F1" in output)
        return

    def test_11_filtered_properties(self):
        """Test that immutability/PreloadWeight are filtered by default"""
        debug.trace(4, f"TestIt.test_11_filtered_properties(); self={self}")
        converter = THE_MODULE.PlasmaConfigConverter()
        converter.parse(SAMPLE_MINIMAL)
        converter.build_model()
        output = converter.convert()
        # These should be filtered out by default
        self.do_assert("immutability=" not in output,
                       "immutability should be filtered by default")
        self.do_assert("PreloadWeight=" not in output,
                       "PreloadWeight should be filtered by default")
        return

    def test_12_is_skippable_key(self):
        """Test is_skippable_key filtering logic"""
        debug.trace(4, f"TestIt.test_12_is_skippable_key(); self={self}")
        self.do_assert(THE_MODULE.is_skippable_key("PreloadWeight", "0"))
        self.do_assert(THE_MODULE.is_skippable_key("immutability", "1"))
        self.do_assert(THE_MODULE.is_skippable_key("DialogHeight", "540"))
        self.do_assert(THE_MODULE.is_skippable_key("DialogWidth", "720"))
        self.do_assert(not THE_MODULE.is_skippable_key("plugin", "org.kde.panel"))
        self.do_assert(not THE_MODULE.is_skippable_key("location", "4"))
        return

    def test_13_with_real_file(self):
        """Test with actual sample file if available"""
        debug.trace(4, f"TestIt.test_13_with_real_file(); self={self}")
        sample_dir = os.path.join(os.path.dirname(__file__), "..")
        sample_file = os.path.join(sample_dir,
                                   "_plasma-org.kde.plasma.desktop-appletsrc.02Mar26.original")
        if not os.path.exists(sample_file):
            pytest.skip("Sample file not available")
        text = system.read_file(sample_file)
        converter = THE_MODULE.PlasmaConfigConverter()
        converter.parse(text)
        converter.build_model()
        output = converter.convert()
        converter.validate_fidelity()
        # Should have zero unaccounted properties
        unaccounted = len(converter.original_properties) - len(converter.accounted_indices)
        self.do_assert(unaccounted == 0,
                       f"Expected 0 unaccounted for real file, got {unaccounted}")
        # Should contain Panel and Taskmanager containers
        self.do_assert("[Container: Panel" in output)
        self.do_assert("plugin=org.kde.plasma.taskmanager" in output)
        return


#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
