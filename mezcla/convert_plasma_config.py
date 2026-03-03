#! /usr/bin/env python3
#
# convert_plasma_config.py: Convert KDE plasma-org.kde.plasma.desktop-appletsrc
# from nested containment-style INI format to a flat relational "Container" format.
#
# This replaces volatile numeric IDs with descriptive functional labels and
# restructures the nested tree into flat blocks linked by sub-container declarations.
#
# Note: See convert_plasma_config.pdf for detailed specification.
#

"""
Convert KDE plasma desktop appletsrc configuration to intuitive Container format.

The input uses nested INI-style sections like [Containments][35][Applets][55]
with numeric IDs. The output replaces these with descriptive labels (e.g.,
[Container: Panel (screen:1)]) and uses sub-container declarations for
parent-child relationships.

Sample usage:
   {script} plasma-org.kde.plasma.desktop-appletsrc
   {script} version_a.conf > version_a.tree
   diff <({script} version_a.conf) <({script} version_b.conf)
"""

# Standard modules
import re
import sys
from collections import OrderedDict
from typing import Optional

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla import system

debug.trace(5, f"global __doc__: {__doc__}")
debug.assertion(__doc__)

# Constants
TL = debug.TL

# Location mapping for panel positions
LOCATION_MAP = {
    "0": "floating",
    "1": "desktop",
    "2": "fullscreen",
    "3": "top",
    "4": "bottom",
    "5": "left",
    "6": "right",
}

# Form factor mapping
FORMFACTOR_MAP = {
    "0": "planar",
    "1": "mediacenter",
    "2": "horizontal",
    "3": "vertical",
    "4": "application",
}

# Environment options
INCLUDE_PRELOAD = system.getenv_bool(
    "INCLUDE_PRELOAD", False,
    description="Include PreloadWeight settings in output")
INCLUDE_DIALOG = system.getenv_bool(
    "INCLUDE_DIALOG", False,
    description="Include ConfigDialog settings in output")
INCLUDE_IMMUTABILITY = system.getenv_bool(
    "INCLUDE_IMMUTABILITY", False,
    description="Include immutability settings in output")


#-------------------------------------------------------------------------------

def simplify_plugin_name(plugin):
    """Convert plugin ID like 'org.kde.plasma.taskmanager' to 'TaskManager'"""
    if not plugin:
        return "Unknown"
    # Strip common prefixes
    name = plugin
    for prefix in ["org.kde.plasma.private.", "org.kde.plasma.", "org.kde."]:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    # Convert to CamelCase
    parts = re.split(r'[._-]', name)
    return "".join(p.capitalize() for p in parts if p)


def parse_section_header(header):
    """Parse INI section header into list of bracket components.
    E.g., '[Containments][35][Applets][55][Configuration][General]'
    => ['Containments', '35', 'Applets', '55', 'Configuration', 'General']
    """
    components = re.findall(r'\[([^\]]+)\]', header)
    debug.trace(6, f"parse_section_header({header!r}) => {components}")
    return components


def is_skippable_key(key, value):
    """Check if a key-value pair should be excluded from output based on env settings"""
    if not INCLUDE_PRELOAD and key == "PreloadWeight":
        return True
    if not INCLUDE_IMMUTABILITY and key == "immutability":
        return True
    if not INCLUDE_DIALOG and key in ("DialogHeight", "DialogWidth"):
        return True
    return False


class PlasmaConfigConverter:
    """Converts KDE plasma desktop config from containment-style to relational format"""

    def __init__(self):
        """Initialize converter state"""
        debug.trace(TL.VERBOSE, "PlasmaConfigConverter.__init__()")
        # Raw parsed sections: key = tuple of header components, value = OrderedDict of props
        self.sections = OrderedDict()
        # Containment data indexed by containment ID
        self.containments = {}
        # Applet data indexed by (containment_id, applet_id)
        self.applets = {}
        # SystrayContainmentId mapping: systray_containment_id -> parent_containment_id
        self.systray_map = {}
        # Non-containment sections (ActionPlugins, ScreenMapping, etc.)
        self.other_sections = OrderedDict()
        # Track all original keys for fidelity validation
        self.original_key_count = 0
        self.output_key_count = 0

    def parse(self, text):
        """Parse INI-style plasma config text into sections"""
        debug.trace(TL.DETAILED, f"PlasmaConfigConverter.parse(): len={len(text)}")
        current_section = None
        for line in text.splitlines():
            line = line.rstrip()
            if not line:
                continue
            if line.startswith('['):
                current_section = line
                if current_section not in self.sections:
                    self.sections[current_section] = OrderedDict()
            elif '=' in line and current_section:
                key, _, value = line.partition('=')
                self.sections[current_section][key] = value
                self.original_key_count += 1
            else:
                debug.trace(4, f"Skipping unparseable line: {line!r}")

    def build_model(self):
        """Build internal data model from parsed sections"""
        debug.trace(TL.DETAILED, "PlasmaConfigConverter.build_model()")

        for section_header, props in self.sections.items():
            components = parse_section_header(section_header)

            if not components:
                continue

            # Handle non-Containments sections
            if components[0] != "Containments":
                self.other_sections[section_header] = props
                continue

            if len(components) < 2:
                continue

            cont_id = components[1]

            # Ensure containment entry exists
            if cont_id not in self.containments:
                self.containments[cont_id] = {
                    "props": OrderedDict(),
                    "applet_ids": [],
                    "config": OrderedDict(),
                    "general": OrderedDict(),
                    "config_dialog": OrderedDict(),
                }

            cont = self.containments[cont_id]

            if len(components) == 2:
                # [Containments][ID] - containment-level properties
                cont["props"].update(props)

            elif len(components) == 3:
                subsection = components[2]
                if subsection == "Configuration":
                    cont["config"].update(props)
                elif subsection == "General":
                    cont["general"].update(props)
                elif subsection == "ConfigDialog":
                    cont["config_dialog"].update(props)
                else:
                    # Other subsection like Wallpaper, etc.
                    cont_key = f"[{subsection}]"
                    for k, v in props.items():
                        cont["props"][f"{cont_key}.{k}"] = v

            elif len(components) >= 4 and components[2] == "Applets":
                applet_id = components[3]
                applet_key = (cont_id, applet_id)

                if applet_key not in self.applets:
                    self.applets[applet_key] = {
                        "props": OrderedDict(),
                        "config": OrderedDict(),
                        "general": OrderedDict(),
                        "config_dialog": OrderedDict(),
                        "shortcuts": OrderedDict(),
                        "extra_sections": OrderedDict(),
                    }
                    cont["applet_ids"].append(applet_id)

                applet = self.applets[applet_key]

                if len(components) == 4:
                    # [Containments][ID][Applets][AID]
                    applet["props"].update(props)
                elif len(components) == 5:
                    sub = components[4]
                    if sub == "Configuration":
                        applet["config"].update(props)
                    elif sub == "Shortcuts":
                        applet["shortcuts"].update(props)
                    else:
                        for k, v in props.items():
                            applet["extra_sections"][f"[{sub}].{k}"] = v
                elif len(components) >= 6:
                    # e.g., [Configuration][General], [Configuration][Appearance], etc.
                    sub_path = ".".join(f"[{c}]" for c in components[4:])
                    if components[4] == "Configuration" and len(components) == 6:
                        sub = components[5]
                        if sub == "General":
                            applet["general"].update(props)
                        elif sub == "ConfigDialog":
                            applet["config_dialog"].update(props)
                        elif sub == "Shortcuts":
                            applet["shortcuts"].update(props)
                        else:
                            for k, v in props.items():
                                applet["extra_sections"][f"[{sub}].{k}"] = v
                    else:
                        for k, v in props.items():
                            applet["extra_sections"][f"{sub_path}.{k}"] = v

            elif len(components) >= 3:
                # Handle deeper containment subsections (e.g., Wallpaper)
                sub_path = ".".join(f"[{c}]" for c in components[2:])
                for k, v in props.items():
                    cont["props"][f"{sub_path}.{k}"] = v

        # Build systray mapping
        for applet_key, applet in self.applets.items():
            systray_id = applet["config"].get("SystrayContainmentId")
            if systray_id:
                self.systray_map[systray_id] = applet_key
                debug.trace(5, f"SystrayContainmentId: {systray_id} -> applet {applet_key}")

    def _make_containment_label(self, cont_id):
        """Generate descriptive label for a containment"""
        cont = self.containments[cont_id]
        plugin = cont["props"].get("plugin", "unknown")
        screen = cont["props"].get("lastScreen", "?")
        location = cont["props"].get("location", "")
        location_str = LOCATION_MAP.get(location, location)

        simple_name = simplify_plugin_name(plugin)

        # Add screen/location info for panels
        if "panel" in plugin.lower():
            return f"{simple_name} (screen:{screen}, location:{location_str})"
        elif "systemtray" in plugin.lower():
            # Check if this systray is owned by a panel
            if cont_id in self.systray_map:
                parent_cont_id, _ = self.systray_map[cont_id]
                parent_plugin = self.containments.get(parent_cont_id, {}).get("props", {}).get("plugin", "")
                parent_screen = self.containments.get(parent_cont_id, {}).get("props", {}).get("lastScreen", "?")
                return f"{simple_name} (panel-screen:{parent_screen})"
            return f"{simple_name} (screen:{screen})"
        elif "folder" in plugin.lower() or "desktop" in plugin.lower():
            activity = cont["props"].get("activityId", "")
            short_activity = activity[:8] if activity else "none"
            return f"{simple_name} (screen:{screen}, activity:{short_activity})"
        else:
            return f"{simple_name} (screen:{screen})"

    def _make_applet_label(self, cont_id, applet_id):
        """Generate descriptive label for an applet"""
        applet_key = (cont_id, applet_id)
        applet = self.applets.get(applet_key, {})
        plugin = applet.get("props", {}).get("plugin", "unknown")
        simple_name = simplify_plugin_name(plugin)

        # Add parent context for disambiguation
        cont = self.containments.get(cont_id, {})
        parent_screen = cont.get("props", {}).get("lastScreen", "?")
        return f"{simple_name} (panel-screen:{parent_screen})"

    def _emit_props(self, props, prefix=""):
        """Format properties as key=value lines, filtering as configured"""
        lines = []
        for key, value in props.items():
            full_key = f"{prefix}{key}" if prefix else key
            if not is_skippable_key(key, value):
                lines.append(f"{full_key}={value}")
                self.output_key_count += 1
            else:
                self.output_key_count += 1  # count as processed even if filtered
        return lines

    def convert(self):
        """Generate the relational Container format output"""
        debug.trace(TL.DETAILED, "PlasmaConfigConverter.convert()")
        output_lines = []

        # Emit non-containment sections first (ActionPlugins, ScreenMapping)
        for section_header, props in self.other_sections.items():
            output_lines.append(section_header)
            for key, value in props.items():
                output_lines.append(f"{key}={value}")
                self.output_key_count += 1
            output_lines.append("")

        # Determine containment ordering: panels first, then desktops, then systrays
        panel_ids = []
        desktop_ids = []
        systray_ids = []
        other_ids = []
        for cont_id, cont in self.containments.items():
            plugin = cont["props"].get("plugin", "")
            if "panel" in plugin.lower() and "systemtray" not in plugin.lower():
                panel_ids.append(cont_id)
            elif "systemtray" in plugin.lower():
                systray_ids.append(cont_id)
            elif "folder" in plugin.lower() or "desktop" in plugin.lower():
                desktop_ids.append(cont_id)
            else:
                other_ids.append(cont_id)

        ordered_ids = panel_ids + desktop_ids + systray_ids + other_ids

        for cont_id in ordered_ids:
            cont = self.containments[cont_id]
            label = self._make_containment_label(cont_id)
            output_lines.append(f"[Container: {label}]")

            # Emit containment properties
            output_lines.extend(self._emit_props(cont["props"]))

            # Emit sub-container references for applets
            applet_order_str = cont["general"].get("AppletOrder", "")
            if applet_order_str:
                ordered_applet_ids = [aid.strip() for aid in applet_order_str.split(";") if aid.strip()]
            else:
                ordered_applet_ids = cont["applet_ids"]

            # Emit all applet IDs (including any not in AppletOrder)
            all_applet_ids = set(cont["applet_ids"])
            for aid in ordered_applet_ids:
                applet_key = (cont_id, aid)
                if applet_key in self.applets:
                    applet = self.applets[applet_key]
                    plugin = applet["props"].get("plugin", "unknown")
                    simple_name = simplify_plugin_name(plugin)
                    output_lines.append(f"sub-container: {simple_name}")
                    all_applet_ids.discard(aid)

            # Emit remaining applets not in AppletOrder
            for aid in cont["applet_ids"]:
                if aid in all_applet_ids:
                    applet_key = (cont_id, aid)
                    if applet_key in self.applets:
                        applet = self.applets[applet_key]
                        plugin = applet["props"].get("plugin", "unknown")
                        simple_name = simplify_plugin_name(plugin)
                        output_lines.append(f"sub-container: {simple_name}")

            # Emit containment config/general (excluding AppletOrder already shown via sub-containers)
            for key, value in cont["config"].items():
                if not is_skippable_key(key, value):
                    output_lines.append(f"{key}={value}")
                self.output_key_count += 1
            for key, value in cont["general"].items():
                if key == "AppletOrder":
                    # Show original AppletOrder for reference
                    output_lines.append(f"AppletOrder={value}")
                elif not is_skippable_key(key, value):
                    output_lines.append(f"{key}={value}")
                self.output_key_count += 1
            for key, value in cont["config_dialog"].items():
                if not is_skippable_key(key, value):
                    output_lines.append(f"[ConfigDialog].{key}={value}")
                self.output_key_count += 1

            output_lines.append("")

            # Emit applet blocks
            for aid in (ordered_applet_ids + [a for a in cont["applet_ids"] if a not in ordered_applet_ids]):
                applet_key = (cont_id, aid)
                if applet_key not in self.applets:
                    continue
                applet = self.applets[applet_key]
                applet_label = self._make_applet_label(cont_id, aid)
                output_lines.append(f"[Container: {applet_label}]")

                plugin = applet["props"].get("plugin", "")
                output_lines.append(f"plugin={plugin}")
                self.output_key_count += 1

                # Emit remaining applet props (skip plugin, already shown)
                for key, value in applet["props"].items():
                    if key == "plugin":
                        continue
                    if not is_skippable_key(key, value):
                        output_lines.append(f"{key}={value}")
                    self.output_key_count += 1

                # Emit config (skip SystrayContainmentId as it's shown as cross-ref)
                for key, value in applet["config"].items():
                    if key == "SystrayContainmentId":
                        systray_cont = self.containments.get(value, {})
                        systray_plugin = systray_cont.get("props", {}).get("plugin", "unknown")
                        output_lines.append(f"systray-ref: {simplify_plugin_name(systray_plugin)}")
                        self.output_key_count += 1
                        continue
                    if not is_skippable_key(key, value):
                        output_lines.append(f"{key}={value}")
                    self.output_key_count += 1

                # Emit general settings (the most important human-readable config)
                output_lines.extend(self._emit_props(applet["general"]))

                # Emit shortcuts
                for key, value in applet["shortcuts"].items():
                    if value:  # skip empty shortcuts
                        output_lines.append(f"[Shortcuts].{key}={value}")
                    self.output_key_count += 1

                # Emit config dialog
                for key, value in applet["config_dialog"].items():
                    if not is_skippable_key(key, value):
                        output_lines.append(f"[ConfigDialog].{key}={value}")
                    self.output_key_count += 1

                # Emit extra sections
                output_lines.extend(self._emit_props(applet["extra_sections"]))

                output_lines.append("")

        return "\n".join(output_lines)

    def validate_fidelity(self):
        """Warn on stderr if any properties were lost"""
        debug.trace(TL.DETAILED, f"validate_fidelity: original={self.original_key_count}, output={self.output_key_count}")
        if self.output_key_count < self.original_key_count:
            lost = self.original_key_count - self.output_key_count
            print(f"WARNING: {lost} key(s) may not be in output "
                  f"(original={self.original_key_count}, processed={self.output_key_count})",
                  file=sys.stderr)
        else:
            debug.trace(TL.VERBOSE, f"Fidelity OK: all {self.original_key_count} keys accounted for")


class Script(Main):
    """Script class for convert_plasma_config"""
    converter: Optional[PlasmaConfigConverter] = None

    def setup(self):
        """Check results of command line processing"""
        debug.trace(TL.VERBOSE, f"Script.setup(): self={self}")
        self.converter = PlasmaConfigConverter()
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def run_main_step(self):
        """Main processing step: read entire input and convert"""
        debug.trace(5, f"Script.run_main_step(): self={self}")
        text = self.read_entire_input()
        if not text:
            system.print_stderr("Error: no input data")
            return

        self.converter.parse(text)
        self.converter.build_model()
        output = self.converter.convert()
        print(output)
        self.converter.validate_fidelity()


#-------------------------------------------------------------------------------

def main():
    """Entry point"""
    debug.trace(TL.DETAILED, f"main(): script={system.real_path(__file__)}")

    app = Script(
        description=__doc__.format(script=gh.basename(__file__)),
        skip_input=False,
        manual_input=True,
        boolean_options=[
            (INCLUDE_PRELOAD, "Include PreloadWeight settings"),
            (INCLUDE_DIALOG, "Include ConfigDialog settings"),
            (INCLUDE_IMMUTABILITY, "Include immutability settings"),
        ] if False else None,   # env-var controlled, not CLI flags
        float_options=None)
    app.run()

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    main()
