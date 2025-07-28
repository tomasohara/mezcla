#! /usr/bin/env python3
#
# Provides class Main to encompass common script processing. By default, the
# command line arguments are analyzed to determine optional filename, which is
# opened. Then, the input stream is feed line-by-line into the process_line
# method.
#
# Usage example:
#    from main import Main
#
#    class MyMain(Main):
#       def process_line(self, line):
#           if "funny" in line:
#               print("Funny looking line: %s" % line)
#
#    if __name__ == "__main__":
#        MyMain().run()
#    
# Notes:
# - See simple_main_example.py for a non-trivial example.
# - To add command-line arguments, pass corresponding arguments to Main's
#   initialization. For example,
#      Main(boolean_options=["fubar"], 
#           int_options=[("count", "Number of times", 10)]).run()
# - As the class likely will just be instantiated once, initialization
#   can be simplfied by using class-level variables for options, as follows:
#      Script(Main):
#          count = 5
#          fubar = False
#          def setup(self):
#              fubar = self.get_parsed_option("fubar")
# - With non-trivial command processing (e.g., positional arguments), it 
#   might be better to do this in the constructor, as follows:
#       def __init__(*args, **kwargs) -> None:
#           super().__init__(*args, positional_options=["targets"], 
#                            **kwargs)
# - Changes to temporary directory/file support should be synchronized with the
#   unit testing base class (see tests/unittest_wrapper.py.
# - Overriding the temporary directory can be handy during debugging (via
#   TEMP_BASE or TEMP_FILE). If you invoke sub-scripts, you might need to
#   specify different ones, as in adhoc/optimize_company_extraction.py.
# - During page-tracking mode, the page numbers are set based on occurrence of
#   form feed characters: \f (n.b., same as ^L and 0x0c).
# - A form feed is treated as an implicit paragraph break: see read_input.
# - The input processing can be used in non-Main scripts by creating a
#   dummy instance and then calling read_input (see randomize_lines.py):
#      dummy = Main([]);   dummy.input_stream = str
#      for line in dummy.process_input(): ...
#
# Note:
# - PERL_SWITCH_PARSING allows for Perl-style -var=val command switches. This 
#   was added to facilitate porting Perl scripts, especially those used in aliases. See
#      https://github.com/tomasohara/shell-scripts/blob/main/tomohara-aliases.bash
#   For example, https://github.com/tomasohara/shell-scripts/blob/main/check_errors.py.
# - This requires a workaround due to an argparse limitation:
#      https://github.com/spotify/luigi/issues/193 [boolean as command-line arg]
#
# TODO:
# - * Clarify TEMP_BASE vs. TEMP_FILE usage.
# - ** Create cheatsheet for argparse tricks (e.,g., using argparse.SUPPRESS to hide).
# - Specify argument via input dicts, such as in 
#      options=[{"name": "fubar", "type": bool}, 
#               {"name": "count", type: int, default: 10}]
# - Add support for perl-style paragraph mode in input processing.
# - Add support for multple input files (e.g., via fileinput module).
# - Add support for csv.csv_reader (see usage in cut.py).
# - Add support for argument aliases (e.g., --input-delim for --delim).
# - Have option for processing text by page by page, instead of
#   just tracking page number with
# - Clarify the input processing in various modes: line, paragraph and file-input.
# - Add function for getting temp_base as dir:
#       dummy_app = Main([], use_temp_base_dir=True)
#       temp_wav_path = gh.form_path(dummy_app.temp_base, "sample.wav")
# - Remove obsolete pylint disable specs (e.g., unbalanced-tuple-unpacking).
#

"""Module for encapsulating main() processing"""

# Standard packages
import argparse
import io
import os
import re
import sys
## OLD: import tempfile
from typing import (
    Optional, List, Tuple, Any, Union,
    Generator, Dict, TextIO,
)
## DEBUG: sys.stderr.write(f"{__file__=}\n")

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla.my_regex import my_re
from mezcla.system import getenv_bool

# Type information
#
# note: Each option/arg is a string label or a tuple with 2-4 elements: (label, desc, default, nargs).
# ex:  'verbose',  ('num', 'number of', 2),  ('files", "File names", ["f1", "f2", "f3"], "+")]
# See Main.convert_option.
##
## TODO?:
## ArgInfoType = Union[str,
##                     Tuple[str, str],
##                     Tuple[str, str, Optional[Any]],
##                     Tuple[str, str, Optional[Any], Optional[str]]]
##
## OLD:
##
## ArgInfoType = Union[str,
##                     Tuple[str],
##                     Tuple[str, Optional[Any]],
##                     Tuple[str, Optional[Any], Optional[Any]],
##                     Tuple[str, Optional[Any], Optional[Any], Optional[Any]]]
##
UserArgInfoType = Union[
    str,
    Tuple[str, str],
    Tuple[str, str, Optional[Any]],
    Tuple[str, str, Optional[Any], Optional[str]]]
SysArgInfoType = Tuple[str, str, Optional[Any], Optional[str]]

# Constants
HELP_ARG = "--help"
USAGE_ARG = "--usage"
VERBOSE_ARG = "verbose"
USE_PARAGRAPH_MODE_DEFAULT = getenv_bool("USE_PARAGRAPH_MODE", False)
USE_PARAGRAPH_MODE = getenv_bool("PARAGRAPH_MODE", USE_PARAGRAPH_MODE_DEFAULT,
                                 "Process input in Perl-style paragraph mode")
FILE_INPUT_MODE = getenv_bool("FILE_INPUT_MODE", False,
                              "Read stdin using Perl-style file input mode--aka file slurping")
debug.assertion(not (USE_PARAGRAPH_MODE and FILE_INPUT_MODE))

FORM_FEED = "\f"
TRACK_PAGES = getenv_bool("TRACK_PAGES", False,
                          "Track page boundaries by form feed--\\f or ^L")
RETAIN_FORM_FEED = getenv_bool("RETAIN_FORM_FEED", False,
                               "Include formfeed (\\f) at start of each segment")
## OLD:
## DEFAULT_FILE_BASE = my_re.sub(r".py\w*$", "", gh.basename(__file__))
## FILE_BASE = system.getenv_text("FILE_BASE", DEFAULT_FILE_BASE,
##                                "Basename for output files including dir")
SHOW_ENV_OPTIONS = system.getenv_bool("ENV_USAGE", debug.detailed_debugging(),
                                      "Include environment options in usage")
# TODO: Put following in common module
INDENT = system.getenv_text("INDENT", "    ",
                            "Indentation for system output")
BRIEF_USAGE = system.getenv_bool("BRIEF_USAGE", False,
                                 "Show brief usage with autohelp")
DURING_ALIAS = system.getenv_bool(
    "DURING_ALIAS", False,
    description="Alias for QUIET_MODE used to support alias in shell-scripts repo")
QUIET_MODE = system.getenv_bool(
    "QUIET_MODE", DURING_ALIAS,
    description="Script should trace less such as stdin processing")
PERL_SWITCH_PARSING = system.getenv_bool("PERL_SWITCH_PARSING", False,
                                         "Preprocess args to expand Perl-style -var[=[val=1]] to --var=val")
## HACK: This is needed if boolean options default to true based on run-time initialization
NEGATIVE_BOOL_ARGS = system.getenv_bool("NEGATIVE_BOOL_ARGS", False,
                                        "Add negation option for each boolean option")
SHORT_OPTIONS = system.getenv_bool("SHORT_OPTIONS", False,
                                   "Automatically derive short options")
ENV_OPTION_PREFIX = system.getenv_value("ENV_OPTION_PREFIX", None,
                                        "Environment variable prefix to check for default")
## TEST
## TEMP_BASE = system.getenv_value("TEMP_BASE", None,
##                                 "Override for temporary file basename")
## OLD: TEMP_BASE = gh.TEMP_BASE
## OLD:
## USE_TEMP_BASE_DIR = system.getenv_bool("USE_TEMP_BASE_DIR", False,
##                                        "Whether TEMP_BASE should be a dir instead of prefix")
USE_TEMP_BASE_DIR = gh.USE_TEMP_BASE_DIR
## TEST
## TEMP_FILE = system.getenv_value("TEMP_FILE", None,
##                                 "Override for temporary filename")
TEMP_FILE = gh.TEMP_FILE
## OLD:
## KEEP_TEMP_FILES = system.getenv_bool("KEEP_TEMP_FILES", debug.detailed_debugging(),
##                                      "Retain temporary files")
KEEP_TEMP_FILES = gh.KEEP_TEMP
INPUT_ERROR_OPTION = "input_error"
INPUT_ERROR = system.getenv_value(
    INPUT_ERROR_OPTION.upper(), None,
    description="Override for strict input processing error handling")
## OLD:
## DISABLE_RECURSIVE_DELETE = system.getenv_value(
##     "DISABLE_RECURSIVE_DELETE", None,
##     description="Disable use of potentially dangerous rm -r style recursive deletions")
DISABLE_RECURSIVE_DELETE = gh.DISABLE_RECURSIVE_DELETE
VERBOSE_DEFAULT = bool(f"--{VERBOSE_ARG}" in sys.argv)
VERBOSE_MODE = system.getenv_value(
    "VERBOSE_MODE", VERBOSE_DEFAULT,
    desc="Default for --verbose")

#-------------------------------------------------------------------------------

class Main(object):
    """Class encompassing common script processing"""
    argument_parser = None
    force_unicode = False
    # TODO: add more class-wide member
    ## temp_base, temp_file
    verbose = False

    def __init__(
            self,
            runtime_args: Optional[List[str]] = None,
            description: Optional[str] = None,
            skip_args: Optional[bool] = None,
            # TODO: Either rename xyz_optiom to match python type name 
            # or rename them without abbreviations.
            # TODO: explain difference between positional_options and positional_arguments
            multiple_files: bool = False,
            use_temp_base_dir: Optional[bool] = None,
            usage_notes: Optional[str] = None,
            program: Optional[str] = None,
            paragraph_mode: Optional[bool] = None,
            track_pages: Optional[bool] = None,
            file_input_mode: Optional[bool] = None,
            newlines: Optional[str] = None,
            boolean_options: Optional[List[UserArgInfoType]] = None,
            text_options: Optional[List[UserArgInfoType]] = None,
            int_options: Optional[List[UserArgInfoType]] = None,
            float_options: Optional[List[UserArgInfoType]] = None,
            positional_options: Optional[List[UserArgInfoType]] = None,
            positional_arguments: Optional[List[UserArgInfoType]] = None,
            skip_input: Optional[bool] = None,
            manual_input: Optional[bool] = None,
            skip_stdin: Optional[bool] = None,
            auto_help: Optional[bool] = None,
            brief_usage: Optional[bool] = None,
            short_options: Optional[bool] = None,
            **kwargs
        ) -> None:
        """Class constructor: parses RUNTIME_ARGS (or command line), with specifications
        for BOOLEAN_OPTIONS, TEXT_OPTIONS, INT_OPTIONS, FLOAT_OPTIONS, and POSITIONAL_OPTIONS
        (see convert_option). Includes options to SKIP_INPUT, or to have MANUAL_INPUT, or to use AUTO_HELP invocation (i.e., assuming {ha} if no args). Also allows for SHORT_OPTIONS.
        Note: SKIP_STDIN makes explicit SKIP_INPUT which gets inferred from MANUAL_INPUT when no specified. This avoids the - argument support that blocks help usage.
        """
        #
        def trace_args(level:int, label:str):
            """Trace out input arguments, each on separate line to simplify diff"""
            debug.trace_expr(level, runtime_args, description, skip_args, multiple_files, use_temp_base_dir, usage_notes, program, paragraph_mode, track_pages, file_input_mode, newlines, boolean_options, text_options, int_options, float_options, positional_options, positional_arguments, skip_input, manual_input, skip_stdin, auto_help, brief_usage, short_options, kwargs, prefix=f"{label}: {{", delim="\n\t", suffix="}", max_len=256)
        #
        debug.trace(4, f"Main.__init__(): self={self}")
        trace_args(5, "input main args")
        self.description = "TODO: what the script does"   # *** DONT'T MODIFY: default TODO note for client
        # note: List[Union[str, Tuple[str, str], Tuple[str, str, str], Tuple[str, str, str, str]]]
        self.boolean_options: List[UserArgInfoType] = []
        self.text_options: List[UserArgInfoType] = []
        self.int_options: List[UserArgInfoType] = []
        self.float_options: List[UserArgInfoType] = []
        self.positional_options: List[UserArgInfoType] = []
        self.process_line_warning = False
        self.input_stream: Optional[TextIO] = None
        self.end_of_page = False
        # TODO: line_num => total_lines_seen AND rel_line_num => line_num
        # TODO: para_num => total_paras_seen AND rel_para_num => para_num
        self.rel_line_num = -1
        self.rel_para_num = -1
        self.page_num = -1
        self.para_num = -1
        self.line_num = -1
        self.char_offset = -1
        self.raw_line: Optional[str] = None
        # note: auto_help is typically used when there is a filename argument
        debug.assertion(not (auto_help and skip_stdin))
        if (auto_help is None):
            ## TODO?: if (all(map(lambda v: v is None, [auto_help, skip_input, manual_input]))):
            ## TEST: auto_help = ((skip_input is None) and (manual_input is None)))
            # Note: auto-help is enabled by default unless no input
            auto_help = ((not skip_input) or manual_input)
            debug.trace(7, f"inferred auto_help: {auto_help}")
        self.auto_help = auto_help      # adds --help to command line if no arguments
        # Note: manual_input was introduced after skip_input to allow for input processing
        # in bulk (e.g., via read_input generator). By default, neither is specified
        # (see template.py), and both should be assumed false.
        # TODO: *** Add better sanity checking (such as a filename on command line).
        if manual_input is None:
            # NOTE: skip_input=>manual_input: T=>T  F=>F  None=>F (i.e., bool(skip_input))
            manual_input = False if (skip_input is None) else skip_input
            debug.trace_fmt(7, "inferred manual_input: {mi}", mi=manual_input)
        self.manual_input = manual_input
        if skip_input is None:
            ## OLD: skip_input = self.manual_input
            skip_input = (self.manual_input or skip_stdin)
            debug.trace_fmt(7, "inferred skip_input: {si}", si=skip_input)
        self.skip_input = skip_input
        #
        self.parser: Optional[argparse.ArgumentParser] = None
        if brief_usage is None:
            brief_usage = BRIEF_USAGE
        self.brief_usage = brief_usage  # show brief usage instead of full --help
        ## OLD:
        ## if auto_help is None:
        ##     ## TODO: rework to be default if none specified for both skip_input and manual_input
        ##     ## OLD: auto_help = self.skip_input
        ##     auto_help = self.skip_input or not self.manual_input
        ##     debug.trace(7, f"inferred auto_help: {auto_help}")
        ## self.auto_help = auto_help      # adds --help to command line if no arguments
        if usage_notes is None:
            usage_notes = ""
        self.notes = usage_notes
        if paragraph_mode is None:
            paragraph_mode = USE_PARAGRAPH_MODE
        self.paragraph_mode = paragraph_mode
        if file_input_mode is None:
            file_input_mode = FILE_INPUT_MODE
        self.file_input_mode = file_input_mode
        self.newlines = newlines
        if track_pages is None:
            track_pages = TRACK_PAGES
        self.track_pages = track_pages
        self.short_options = (short_options if (short_options is not None) else SHORT_OPTIONS)
        if skip_args is None:
            # note: skip_args useful for testing scripts to avoid argument parsine
            skip_args = False
        trace_args(6, "redux main args")

        # Check miscellaneous options
        BINARY_INPUT_OPTION = "binary_input"
        PERL_SWITCH_PARSING_OPTION = "perl_switch_parsing"
        bad_options = system.difference(list(kwargs.keys()), [BINARY_INPUT_OPTION, PERL_SWITCH_PARSING_OPTION, INPUT_ERROR_OPTION])
        debug.assertion(not bad_options, f"Extraneous kwargs: {bad_options}")
        self.binary_input = kwargs.get(BINARY_INPUT_OPTION, False)
        self.input_error_mode = kwargs.get(INPUT_ERROR_OPTION, INPUT_ERROR)

        # Setup temporary file and/or base directory
        # TODO: allow temp_base handling to be overridable by constructor options
        # TODO: reconcile with unittest_wrapper.py.get_temp_dir
        ## OLD:
        ## prefix = (FILE_BASE + "-")
        ## alt_temp_base = (
        ##     tempfile.NamedTemporaryFile(
        ##         prefix=prefix,
        ##         delete=not debug.detailed_debugging(),
        ##         ## TODO: "suffix": "-"
        ##     ).name)
        self.temp_base = gh.get_temp_file()
        # TODO: self.use_temp_base_dir = gh.dir_exists(gh.basename(self.temp_base))
        # -or-: temp_base_dir = system.getenv_text("TEMP_BASE_DIR", " "); self.use_temp_base_dir = bool(temp_base_dir.strip()); ...
        if use_temp_base_dir is None:
            use_temp_base_dir = USE_TEMP_BASE_DIR
        self.use_temp_base_dir = use_temp_base_dir
        if self.use_temp_base_dir:
            ## TODO: gh.full_mkdir
            ## TEMP HACK: remove file if not a dir (n.b., quirk with NamedTemporaryFile
            if system.is_regular_file(self.temp_base):
                gh.delete_file(self.temp_base)
            ## OLD: gh.run("mkdir -p {dir}", dir=self.temp_base)
            gh.full_mkdir(self.temp_base)
            ## TODO3: main-temp.txt???
            default_temp_file = gh.form_path(self.temp_base, "temp.txt")
        else:
            default_temp_file = self.temp_base
        self.temp_file = (TEMP_FILE or default_temp_file)

        # Note: --help assumed for input-less scripts with command line options
        # to avoid inadvertent script processing.
        #
        if ((runtime_args is None) and (not skip_args)):
            # note: there is a quirk when using this with pytest
            debug.assertion(sys.argv[0] != "pytest")
            runtime_args = sys.argv[1:]
            debug.trace(4, f"Using sys.argv[1:] for runtime args: {runtime_args}")
            if self.auto_help and not runtime_args:
                help_arg = (USAGE_ARG if self.brief_usage else HELP_ARG)
                debug.trace(4, f"FYI: Adding {help_arg} to command line (as per auto_help)")
                runtime_args = [help_arg]
        #
        # Process special hook for converting Perl-style switches like -fu=123 to --fu=123
        # See -s option under perlrun man page for enabling this rudimentary switch parsing.
        # Note: mainly just intended for when porting Perl scripts.
        self.perl_switch_parsing = kwargs.get(PERL_SWITCH_PARSING_OPTION, PERL_SWITCH_PARSING)
        if self.perl_switch_parsing and runtime_args:
            debug.trace(4, "FYI: Enabling Perl-style options")
            debug.assertion(not re.search(r"--\w+", " ".join(runtime_args)),
                            "Shouldn't use Python arguments with PERL_SWITCH_PARSING (e.g., mixing types as in -fu --bar)")
            for i, arg in enumerate(runtime_args):
                if arg in ["-", "--"]:
                    break
                if my_re.search(r"^-([a-z0-9_]+\w*)=?(.*)$", arg, flags=re.IGNORECASE):
                    option = my_re.group(1)
                    value = (my_re.group(2) if len(my_re.group(2)) else "1")
                    new_arg = f"--{option}={value}"
                    debug.trace(4, f"Converted Perl-style arg {i} from {arg!r} to {new_arg}")
                    debug.assertion(not system.file_exists(arg))
                    runtime_args[i] = new_arg
                    
        # Get other options
        self.program = program
        if description:
            self.description = description
        if boolean_options:
            self.boolean_options += boolean_options
        # note: adds --verbose unless already specified (TODO: add way to disable)
        boolean_options_proper = []
        for t in self.boolean_options:
            if isinstance(t, str):
                boolean_options_proper.append(t)
            elif isinstance(t, (list, tuple)):
                if isinstance(t[0], str):
                    boolean_options_proper.append(t[0])
        if (VERBOSE_ARG not in boolean_options_proper):
            debug.trace(6, f"Adding --{VERBOSE_ARG} to boolean options {self.boolean_options}")
            self.boolean_options += [(VERBOSE_ARG, "Verbose output mode")]
        if text_options:
            self.text_options = text_options
        if int_options:
            self.int_options = int_options
        if float_options:
            self.float_options = float_options
        if positional_options or positional_arguments:
            # TODO: mark positional_options as deprecated
            debug.assertion(not (positional_options and positional_arguments))
            self.positional_options = positional_options or positional_arguments or []
        self.multiple_files = multiple_files      # sets other_filenames if multiple w/ nargs=+ 
        # Set defaults
        self.parsed_args: Dict[str, Any] = {}
        self.filename = None
        self.other_filenames: List[str] = []
        # Do command-line parsing
        # TODO: consolidate with runtime_args check above
        if not skip_args and runtime_args:
            self.check_arguments(runtime_args)
        debug.trace_current_context(level=debug.QUITE_DETAILED)
        ## OLD:
        debug.trace_object(6, self, label="Main instance")
        ## TEST: debug.trace_object(6, self, label=f"{self.__init__.__qualname__.split('.')[0]} instance")
        debug.trace_fmt(debug.QUITE_DETAILED, "end of Main.__init__(); self={s}",
                        s=self)
        return

    def get_arguments(
            self,
            just_positional: bool = False,
            just_optional: bool = False
        ) -> List[UserArgInfoType]:
        """Return list of arguments, optionally JUST_POSITIONAL and JUST_OPTIONAL"""
        argument_specs = []
        if not just_positional:
            argument_specs += self.boolean_options + self.text_options + self.int_options + self.float_options
        if not just_optional:
            argument_specs += self.positional_options
        ## OLD: arguments = [(spec[0] if list(spec[0]) else spec) for spec in argument_specs]
        arguments = [(spec[0] if isinstance(spec, list) else spec) for spec in argument_specs]
        debug.trace(6, f"get_arguments([pos?={just_positional}, opt?={just_optional}] => {arguments}")
        return arguments
    
    def convert_option(
            self,
            option_spec: UserArgInfoType,
            default_value: Optional[Any] = None,
            positional: bool = False
        ) -> SysArgInfoType:
        """Convert OPTION_SPEC to (label, description, default) tuple. 
        Notes: The description and default of the specification are optional,
        and the parentheses can be omitted if just the label is given. For example,
             ("--num-eggs", "Number of eggs", 2)
        If POSITIONAL, the option prefix (--) is omitted and OPTION_SPEC
        includes an optional nargs component, such as:
             ("other-files", "Other file names", ["f1", "f2", "f3"], "+")
        """
        # EX: label, _desc, _default = Main.convert_option("--mucho-backflips"); label => "--mucho-backflips"
        ## TODO2: add short option support as in ("--num-eggs/-#", "Number of eggs", 2)
        ## TODO3: make the component representation structured (e.g., namedtuple)
        ## TEST: result = ["", "", ""]
        debug.trace_fmtd(6, "in convert_option({o}, {d}, {p})",
                         o=option_spec, d=default_value, p=positional)
        opt_label: str = ""
        opt_desc: str = ""
        opt_default: Any = default_value
        opt_nargs: Optional[str] = None
        opt_prefix = "--" if not positional else ""
        # TODO: use keyword arguments (or namedtuple)
        if isinstance(option_spec, tuple):
            ## OLD: option_components = list(option_spec)
            option_components = option_spec
            opt_label = opt_prefix + option_components[0]
            if len(option_components) > 1:
                opt_desc = option_components[1]
            if len(option_components) > 2:
                opt_default = option_components[2]
            if len(option_components) > 3:
                if positional:
                    opt_nargs = option_components[3]
                else:
                    debug.trace(3, f"Warning: opt_nargs only positional {option_spec!r}")
        else:
            opt_label = opt_prefix + str(option_spec)
        debug.assertion(not " " in opt_label)
        result_list = [opt_label, opt_desc, opt_default, opt_nargs]
        result = tuple(result_list)
        debug.trace_fmtd(5, "convert_option({o}, {d}, {p}): self={s} => {r}",
                         o=option_spec, d=default_value, p=positional,
                         s=self, r=result)
        return result

    def convert_argument(
            self,
            argument_spec: UserArgInfoType,
            default_value: Optional[Any] = None
        ) -> SysArgInfoType:
        """Convert ARGUMENT_SPEC to (label, description, default) tuple. 
        Note: This is a wrapper around convert_option for positional arguments."""
        debug.trace(6, f"convert_argument({argument_spec}, {default_value}")
        return self.convert_option(argument_spec, default_value, positional=True)

    def get_option_name(self, label: str, allow_under: Optional[bool] = None) -> str:
        """Return internal name for parser options (e.g., dashes converted to underscores)
        Note: Unless ALLOW_UNDER, issues warning about underscores used in labels: this is 
        to support standard Unix argument conventions (e.g., "--skip-run" not "--skip_run").
        """
        # EX: dummy_app.get_option_name("mucho-backflips") => "mucho_backflips"
        if not allow_under:
            debug.assertion(("_" not in label), "Use dashes not underscores")
        name = label.replace("-", "_")
        debug.trace_fmtd(6, "get_option_name({l}) => {n}; self={s}",
                         l=label, n=name, s=self)
        return name

    def has_parsed_option_old(self, label: str) -> bool:
        """Whether option for LABEL specified (i.e., non-null value)
        Note: OLD version that checks for non-null value)
        """
        # EX: self.parsed_args = {"it": False}; self.has_parsed_option_old("nonit") => False
        name = self.get_option_name(label)
        has_option = (name in self.parsed_args and (self.parsed_args[name] is not None))
        debug.trace_fmtd(6, "has_parsed_option_old({l}) => {r}",
                         l=label, r=has_option)
        return has_option

    def has_parsed_option(self, label: str) -> Optional[Any]:
        """Value for LABEL specified or None if not applicable
        Note: This is a deprecated method (use get_parsed_option instead)
        """
        # EX: self.parsed_args = {"it": False}; self.has_parsed_option("notit") => None
        ## TEMP HACK: if called by a subclass, treate as alias to get_parsed_option
        if (self.__class__ != "__main__.Script"):
            debug.trace(3, "Warning: deprecated method: has_parsed_option => get_parsed_option")
            return self.get_parsed_option(label)
        # Return parsed-arg entry for the option
        name = self.get_option_name(label)
        ## TEMP HACK: has_parsed_option returns args.get(opt)
        option_value = self.parsed_args.get(name)
        debug.trace_fmtd(6, "has_parsed_option({l}) => {r}",
                         l=label, r=option_value)
        return option_value

    def convert_option_value(self, label: str, value: Any) -> Any:
        """Convert the option LABEL's text VALUE into its type
        Note: boolean options account for symbolic ones like False and off."""
        ## NOTE: added to support type-specific values from environment
        ## TODO2: encode type in tuple associated with each option
        typed_value = value
        for option_info, option_type in [(self.boolean_options, bool),
                                         (self.int_options, int),
                                         (self.float_options, float)]:
            for option_tuple in option_info:
                option_name = (option_tuple[0] if (not isinstance(option_tuple, str)) else option_tuple)
                if label == option_name:
                    typed_value = (system.to_bool(value) if option_type is bool else int(value) if option_type is int else float(value))
                    break
        debug.trace(5, f"convert_option_value({label}, {value!r}) => {typed_value!r}")
        return typed_value
    
    def get_parsed_option(
            self,
            label: str,
            default: Optional[Any] = None,
            positional: bool = False,
            allow_under: Optional[bool] = None
        ) -> Optional[Any]:
        """Get value for option LABEL, with dashes converted to underscores. 
        If POSITIONAL specified, DEFAULT value is used if omitted
        Note: ALLOW_UNDER skips sanity check about underscores
        """
        under_label = label.replace("-", "_")
        dash_label = label.replace("_", "-")
        opt_label = (self.get_option_name(label, allow_under=allow_under) if not positional
                     else label)
        if not self.parsed_args:
            debug.trace(5, "Error: Unexpected condition in get_parsed_option")
            return default
        value = self.parsed_args.get(opt_label)
        if value is None:
            # note: workaround for argparse quirk
            # See https://stackoverflow.com/questions/12834785/having-options-in-argparse-with-a-dash
            alt_label = under_label if positional else dash_label
            value = self.parsed_args.get(alt_label)
            if value:
                debug.trace(4, f"FYI: Resolved for alternative label workaround: {alt_label=} {value=}")
        # Override null value with default
        if value is None:
            if ((default is None) and ENV_OPTION_PREFIX):
                env_var = f"{ENV_OPTION_PREFIX}_{opt_label}".upper()
                default = system.getenv(env_var)
                if default:
                    default = self.convert_option_value(label, default)
                    debug.trace(4, f"FYI: Using option {label} from env ({env_var}: {default!r})")
            value = default
            # Do sanity check for positional argument being checked by mistake
            # TODO: do automatic correction?
            debug.trace_expr(5, label, opt_label, under_label, self.parsed_args)
            if opt_label != label:
                debug.assertion(label not in self.parsed_args)
            elif under_label != label:
                debug.assertion(under_label not in self.parsed_args,
                                f"potential option/argument mismatch for {label}")
            debug.trace_expr(6, label, opt_label, under_label)
        # Return result, after tracing invocation
        debug.trace_fmtd(5, "get_parsed_option({l}, [{d}], [{p}]) => {v}",
                         l=label, d=default, p=positional, v=value)
        return value

    def get_parsed_argument(self, label: str,
                            default: Optional[Any] = None,
                            allow_under: Optional[bool] = None) -> Optional[Any]:
        """Get value for positional argument LABEL using DEFAULT value"""
        debug.trace_fmtd(6, "get_parsed_agument({l}, [{d}])",
                         l=label, d=default)
        ## TODO2: debug.assertion(label in ((l[0] if isinstance(l, list) else l)) for l in self.positional_options)
        is_positional = (label in self.get_arguments(just_positional=True))
        if not is_positional:
            debug.trace(4, f"FYI: Use get_parsed_option for non-positional option {label}")
        return self.get_parsed_option(label, default, positional=is_positional,
                                      allow_under=allow_under)

    def check_arguments(self, runtime_args: List[str]) -> None:
        """Check command-line arguments
        Note: This uses argparse, which might exit the process
        """
        # Note: Shows env. options when debugging as these are backdoor settings.
        debug.trace_fmtd(5, "Main.check_arguments({args})", args=runtime_args)
        # TODO: add in detailed usage notes w/ environment option descriptions (see google_word2vec.py)
        if not self.argument_parser:
            self.argument_parser = argparse.ArgumentParser
        usage_notes = self.notes
        ## OLD: if (not usage_notes and SHOW_ENV_OPTIONS):
        if (not usage_notes):
            env_opt_spec = ""
            if (SHOW_ENV_OPTIONS or VERBOSE_MODE):
                env_opts = system.formatted_environment_option_descriptions(sort=True, indent=INDENT)
                env_opt_spec = f"- Available env. options:\n{INDENT}{env_opts}"
            elided_path = re.sub(r"^.*/", ".../", sys.argv[0])
            # note: A dash ("-") is used to indicate stdin with filename arg or to bypass usage w/o one
            # TODO1: get dash put in usage to make more explicit, such as in following:
            #     usage: main.py [-h] [--verbose] [filename] [-]
            usage_notes = ("Notes: \n"
                           + ("- Use - for filename to skip usage (i.e., a la stdin).\n" if (not self.skip_input)
                              else "- Use - to skip usage if no arguments needed.\n" if self.auto_help else "")
                           + ("- Use --non-... for any boolean arg\n" if NEGATIVE_BOOL_ARGS else "")
                           + (f"- Use \"ENV1='v1' ENV2='v2' python {elided_path} ...\" for environment options.\n")
                           + env_opt_spec)
        parser = self.argument_parser(description=self.description,
                                      epilog=usage_notes, prog=self.program,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
        # TODO: use capitalized script description but lowercase argument help

        def add_argument(opt_label: str, add_short: Optional[bool] = None, **kwargs) -> None:   # pylint: disable=redefined-builtin
            """Wrapper around argparse.ArgumentParser.add_argument
            Note: adds short options string if ADD_SHORT (see self.short_options)"""
            debug.trace(6, f"add_argument{(opt_label, add_short, kwargs)}")
            if add_short is None:
                add_short = self.short_options
            if add_short and my_re.search(r"-(-[a-z])[a-z]+", opt_label):
                short_label = my_re.group(1)
                parser.add_argument(short_label, opt_label, **kwargs)
            else:
                parser.add_argument(opt_label, **kwargs)

        # Check for options of specific types
        # TODO: consolidate processing for the groups; add option for environment-based default; resolve stupid pylint false positive about unbalanced-tuple-unpacking
        for opt_spec in self.boolean_options:
            # pylint: disable=unbalanced-tuple-unpacking
            (opt_label, opt_desc, opt_default, _opt_nargs) = self.convert_option(opt_spec, None)
            if self.perl_switch_parsing:
                # note: With Perl argument support, booleans treated as integers due to argparse quirk.
                ## TEST: parser.add_argument(opt_label, type=int, nargs="?", default=opt_default, help=opt_desc)
                numeric_default = 1 if opt_default else 0
                add_argument(opt_label, type=int, default=numeric_default, help=opt_desc)
            else:
                add_argument(opt_label, default=opt_default, action="store_true", help=opt_desc)
                if NEGATIVE_BOOL_ARGS:
                    # BAD: label = f"non-{opt_label}"
                    under_label = my_re.sub(r"^__", "", opt_label.replace("-", "_"))
                    label = "--non-" + under_label
                    ## SO-SO
                    ## # note: converts "Description ..." into "Do not description ..."
                    ## opt_desc_uncapitalized = ((opt_desc[:1].lower() + opt_desc[1:]) if opt_desc else "")
                    ## desc = f"Non {opt_desc_uncapitalized}"
                    # note: the argument is not shown in help to avoid clutter
                    desc = argparse.SUPPRESS
                    debug.trace(4, f"Adding negative-boolean: label={label} dest={under_label}")
                    parser.add_argument(label, default=opt_default, dest=under_label, action="store_false", help=desc, add_short=False)
        ## OLD:
        ## for opt_spec in self.int_options:
        ##     (opt_label, opt_desc, opt_default, _) = self.convert_option(opt_spec, None)    # pylint: disable=unbalanced-tuple-unpacking
        ##     add_argument(opt_label, type=int, default=opt_default, help=opt_desc)
        ## for opt_spec in self.float_options:
        ##     (opt_label, opt_desc, opt_default, _) = self.convert_option(opt_spec, None)    # pylint: disable=unbalanced-tuple-unpacking
        ##     add_argument(opt_label, type=float, default=opt_default, help=opt_desc)
        ## for opt_spec in self.text_options:
        ##     (opt_label, opt_desc, opt_default, _) = self.convert_option(opt_spec, None)    # pylint: disable=unbalanced-tuple-unpacking
        ##     add_argument(opt_label, default=opt_default, help=opt_desc)
        for options, opt_type in [(self.int_options, int),
                                  (self.float_options, float),
                                  (self.text_options, str)]:
            # pylint: disable=unbalanced-tuple-unpacking
            for opt_spec in options:
                (opt_label, opt_desc, opt_default, _opt_nargs) = self.convert_option(opt_spec, None)
                add_argument(opt_label, type=opt_type, default=opt_default, help=opt_desc)

        # Add dummy arguments
        # Note: These are used as reminders on how to flesh out the initialization
        if debug.detailed_debugging():
            if not self.boolean_options:
                parser.add_argument("--TODO-bool-arg", default=False, action="store_true",
                                    help="Add via boolean_options keyword")
            if not self.text_options:
                parser.add_argument("--TODO-text-arg", default="",
                                    help="Add via text_options keyword")
            if not self.int_options:
                parser.add_argument("--TODO-int-arg", type=int, default=0,
                                    help="Add via int_options keyword")
            if not self.float_options:
                parser.add_argument("--TODO-float-arg", default=0.0,
                                    help="Add via float_options keyword")

        # Add positional arguments
        for i, opt_spec in enumerate(self.positional_options):
            opt_label, opt_desc, opt_default, opt_nargs = self.convert_argument(opt_spec, "") # pylint: disable=unbalanced-tuple-unpacking
            # note: a numeric nargs produces a list even if 1, so None used by default
            nargs = opt_nargs
            debug.trace_fmtd(6, "positional arg {i}, nargs={nargs}", 
                             i=i, nargs=nargs)
            # TODO: add default to opt_desc if not mentioned
            parser.add_argument(opt_label, default=opt_default, nargs=nargs, 
                                help=opt_desc)

        # Add filename last and make optional with "-" default (i.e., for stdin)
        # Note: with nargs=+, the result is a list of filenames (even if one file [WTH?]!)
        if not self.skip_input:
            filename_nargs = ("?" if (not self.multiple_files) else "+")
            debug.trace_fmtd(6, "filename_nargs={nargs}", nargs=filename_nargs)
            parser.add_argument("filename", nargs=filename_nargs, default="-",
                                help="Input filename")
        elif self.auto_help:
            dash_nargs = "?"
            debug.trace_expr(6, dash_nargs)
            ## TAKE1:
            ## TODO2: hide [dash] from usage (maldito argparse)
            ## parser.add_argument("dash", nargs=dash_nargs, default="-",
            ##                     help="Use - to bypass usage statement")
            parser.add_argument("-", dest="_", help=argparse.SUPPRESS,
                                default="-", action="store_true")
            ## TODO3
            ## parser.add_argument("--", dest="_", help=argparse.SUPPRESS,
            ##                     default="-", action="store_true")
            ## NOTE: currently leads to "error: unrecognized arguments: --" unlike when - used
        else:
            debug.trace(6, "Not adding filename nor dash argument")

        # Optionally, show brief usage and exit
        # note: print_usage just prints command line synopsis (not individual descriptions)
        if (self.brief_usage and (runtime_args == [USAGE_ARG])):
            debug.trace(4, "Just showing (brief) usage and then exiting")
            debug.trace(5, "warning: self.setup won't be invoked")
            parser.print_usage()

            # Show streamlined example (e.g., using first if more than one)
            # exs: "Sample usages:\n   echo $'stupid pet tricks.*"
            # and: "Typical example:\n   some_script.py - <<<"Hey, Joe..."
            if my_re.search(r"^.*(usage|example)s?:\s*\n(.*)", self.description,
                            flags=my_re.IGNORECASE|my_re.MULTILINE):
                simple_usage = my_re.group(2)
                simple_usage = my_re.sub(r"\n\s*\n.*", "", simple_usage)
                print("example:\n{ex}".format(ex=gh.indent(simple_usage)))
            sys.exit()

        # Parse the command line and get result
        debug.trace_fmtd(6, "parser={p}", p=parser)
        debug.trace_object(8, parser, max_depth=2)
        self.parser = parser
        # note: not trapped to allow for early exit
        self.parsed_args = vars(parser.parse_args(runtime_args))
        debug.trace(5, f"parsed_args = {self.parsed_args}")
        self.verbose = bool(self.get_parsed_option("verbose", VERBOSE_MODE))
        # Get filename unless input ignored and fixup if returned as list
        # TODO: add an option to retain self.filename as is
        if not self.skip_input:
            self.filename = self.parsed_args["filename"]
            if (isinstance(self.filename, list)):
                if not self.multiple_files:
                    debug.trace(3, "Warning: Making (list) self.filename a string & setting self.other_filenames to remainder")
                file_list = self.filename
                self.other_filenames = file_list[1:]
                self.filename = file_list[0] if len(file_list) else "-"
        debug.trace(6, "end Main.check_arguments()")
        return

    def setup(self) -> None:
        """Perform script setup prior to input processing
        Note: This is not invoked if the script exits during --help processing"
        """
        # Note: Use for post-argument proceessing setup
        debug.trace_fmtd(5, "Main.setup() stub: self={s}", s=self)
        return

    def process_line(self, line: str) -> None:
        """Stub for input processing that just prints the input.
        Note: issues error message about required specialization"""
        # NOTE: the trailing newline is omitted
        # TODO: clarify stripped newline vs. no newline at end of file
        debug.trace_fmt(5, "Main.process_line({l})", l=line)
        if not self.process_line_warning:
            system.print_stderr("Warning: need to specialize process_line (i.e., stub called)")
            self.process_line_warning = True
        print(line)
        return

    def run_main_step(self) -> None:
        """Stub for main processing, along with error message"""
        # TODO: use decorator (e.g., @abstract)
        debug.trace_fmtd(5, "Main.run_main_step(): self={s}", s=self)
        system.print_stderr("Internal error: specialize run_main_step")
        return

    def init_input(self) -> None:
        """Resolve input stream from either explicit filename or via standard input.
        Note: self.newlines is used to override stream (e.g., so \r not treated as line delim).
        Aside: The manual_input/skip_input logic is a bit convoluted, so an expedient
        to disable input processing entirely is to override in subclass (e.g., no-op).
        """
        ## TODO3: cleanup manual_input/skip_input dependencies
        debug.trace(5, "Main.init_input()")
        self.input_stream = sys.stdin
        if (self.filename and (self.filename != "-")):
            if (isinstance(self.filename, list) or (len(self.other_filenames) > 0)):
                debug.assertion(self.filename != ["-"])
                if not self.multiple_files:
                    # note: check_arguments sets self.other_filenames
                    debug.trace(3, "Warning: Not opening multiple-valued filename arg")
                    debug.trace_expr(3, self.filename, self.other_filenames)
            else:
                debug.assertion(isinstance(self.filename, str))
                if not (self.manual_input and self.skip_input):
                    debug.assertion(os.path.exists(self.filename))
                    mode = ("r" if (not self.binary_input) else "rb")
                    self.input_stream = system.open_file(self.filename, mode=mode,
                                                         errors=self.input_error_mode)
                    debug.assertion(self.input_stream)
        # Optionally reopen stream to change built-in settings
        error_handling_change = (self.input_error_mode
                                 and (self.input_error_mode != self.input_stream.errors))
        reopen_stream = (error_handling_change or self.newlines)
        if reopen_stream and self.input_stream:
            if self.newlines:
                debug.trace(4, f"Changing input stream newlines from {self.input_stream.newlines!r} to {self.newlines!r}")
            if error_handling_change:
                debug.trace(4, f"Changing input stream error handling from {self.input_stream.errors!r} to {self.input_error_mode!r}")
            ## TODO3: track down mypy issue with following call:
            ##   Item "TextIO" of "TextIO | Any" has no attribute "write_through"  [union-attr]
            self.input_stream = io.TextIOWrapper(
                self.input_stream.buffer, encoding=self.input_stream.encoding,
                errors=self.input_error_mode, newline=self.newlines,
                line_buffering=bool(self.input_stream.line_buffering),
                write_through=self.input_stream.write_through)        # type: ignore [union-attr]
            debug.trace_object(4, self.input_stream)
    
    def run(self) -> None:
        """Runner for script processing"""
        debug.trace(5, "Main.run()")
        # TODO: decompose (e.g., isolate input proecessing)

        # Have client do pre-input initialization (e.g., argument extraction)
        self.setup()

        # Initiate the main input processing
        ## TODO3: skip initialize if skip_input (i.e., rework manual_input/skip_input logic)
        self.init_input()
        try:
            # If not automatic input, process the main step of script
            if self.manual_input:
                self.run_main_step()
            # Otherwise have client process input line by line
            else:
                debug.assertion(not self.skip_input)

                # TODO: Trace status only if script blocks waiting for user
                if not QUIET_MODE:
                    debug.trace(2, "Processing input")
                self.process_input()
        except BrokenPipeError:
            ## TODO: exit gracefully (e.g., after wrap_up)
            ## debug.trace_fmt(6, "Silly exception processing input: {exc}", 
            ##                 exc=system.get_exception)
            ##
            ## exit("Note: you can Ignore any silly BrokenPipeError"s thrown by Python!")
            ##
            ## pass
            ##
            ## take 3+:
            ## Based on https://stackoverflow.com/questions/26692284/how-to-prevent-brokenpipeerror-when-doing-a-flush-in-python
            ## sys.stderr.close()                       [doesn"t work for Python 3]
            ##
            ## take 4 [gotta hate Python!]:
            # Python flushes standard streams on exit; redirect remaining output
            # to devnull to avoid another BrokenPipeError at shutdown
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
            sys.exit(1)  # Python exits with error code 1 on EPIPE

        # Invoke client end processing
        self.wrap_up()

        # Remove any temporary files
        self.clean_up()
        return

    def read_entire_input(self) -> Union[str, bytes]:
        """Returns all input (either from specified filename or stdin)
        Notes:
        - This is simple alternative to the read_input generator intended for use with dummy_app
        - Another alternative is to invoke self.init_input and then use self.input_stream
        """
        debug.trace(5, "Main.read_entire_input()")
        self.init_input()
        if not QUIET_MODE:
            debug.trace(2, "Processing entire input")
        debug.trace_object(4, self.input_stream)
        if self.input_stream:
            input_text = self.input_stream.read()
        else:
            input_text = ""
        debug.trace_expr(6, input_text)
        return input_text
    
    def read_input(self) -> Generator[str, None, None]:
        """Generator for producing lines of text from the input (without newlines).
        Notes:
        0. Use read_entire_input for method to return all text at once (i.e., non-generator).
        1. This is called automatically via process_input.
        2. When page mode is in effect, 
           a. lines don"t include form feeds
           b. pages are not buffered: the page number is just tracked.
        3. Paragraph end at empty lines or form feeds (i.e., implicit).
        """
        # TODO: add special page-input mode
        # Note: para_num reset here and updated by process_input
        debug.trace_fmtd(5, "Main.read_input(): {input}",
                         input=self.input_stream)

        if not self.input_stream:
            debug.trace(4, "Warning: No input stream in read_input")
            return

        # Optionally return input all at once
        # Note: Final newline is removed, as this feeds into process_line,
        # which there was one
        if self.file_input_mode:
            contents = self.input_stream.read()
            if contents.endswith("\n"):
                contents = contents[:-1]
            debug.trace_fmt(6, "yielding entire file [Par1/L1]: {c}",
                            c=contents)
            yield contents
            return

        # Start line-based input
        self.page_num = 1
        self.para_num = 1
        self.rel_para_num = 1
        self.line_num = 0
        self.rel_line_num = 0
        self.char_offset = 0
        for line in self.input_stream:
            self.rel_line_num += 1
            self.line_num += 1
            self.raw_line = line
            if line.endswith("\n"):
                line = line[:-1]
            debug.trace_fmt(6, "L{n}: {l}", n=self.line_num, l=line)
            if self.force_unicode:
                debug.trace(4, "Warning: Main.force_unicode obsolete")
            ## TEST: debug.trace(7, f"\ttype(line): {type(line)}; offset={self.input_stream.tell()}")
            if self.track_pages:
                for i, line_segment in enumerate(line.split(FORM_FEED)):
                    debug.trace(7, f"LS{i}: {line_segment}")
                    self.end_of_page = False
                    if i == 0:
                        self.end_of_page = (line != line_segment)
                    else:
                        self.end_of_page = True
                        if RETAIN_FORM_FEED:
                            line_segment = FORM_FEED + line_segment
                    ## OLD: if line_segment and (i > 0):
                    ## NEW:
                    if (i > 0):
                        self.line_num += 1
                        self.rel_line_num += 1
                        if self.end_of_page:
                            self.page_num += 1
                            self.rel_para_num = 1
                            self.rel_line_num = 1
                    ## OLD: if line_segment:
                    ## NEW:
                    if True:            # pylint: disable=using-constant-test
                        debug.trace_fmt(6, "yielding line segment [Pg{pg}/Par{par}/L{ln}]: {ls}",
                                        pg=self.page_num, par=self.rel_para_num, ln=self.rel_line_num, ls=line_segment)
                        yield line_segment
                    self.char_offset += len(line_segment)
                    debug.trace_expr(7, self.page_num)
                if (line != self.raw_line):
                    self.char_offset += 1
            else:
                debug.trace_fmt(6, "yielding line [Par{par}/L{lnum}]: {l}",
                                par=self.rel_para_num, lnum=self.rel_line_num, l=line)
                yield line
                if self.raw_line is not None:
                    self.char_offset += len(self.raw_line)
        return

    def is_line_mode(self) -> bool:
        """Whether processing normal lines (not paragraphs or entire files)"""
        return  (not (self.paragraph_mode or self.file_input_mode))

    def process_input(self) -> None:
        """Process each line in current input stream (or stdin):
        Note: if paragraph mode enabled the input is processed in groups of lines separated by an entirely blank line (i.e., length is 0)"""
        # Note: self.raw_line can be used to check for missing newline at end of file
        debug.trace_fmtd(5, "Main.process_input(): {input}",
                         input=self.input_stream)
        self.rel_line_num = 0
        if self.paragraph_mode:
            self.para_num = 0
        paragraph = ""
        last_line = None
        line_mode = self.is_line_mode()
        debug.assertion(debug.xor3(line_mode, self.paragraph_mode, self.file_input_mode))

        # Read next line (or line segment if in page mode and form feed in line)
        for line in self.read_input():
            # Process as is if in regular line mode
            if (line_mode or self.file_input_mode):
                self.process_line(line)
                if line_mode:
                    debug.assertion("\n" not in line)

            # Process non-empty lines grouped together if in paragraph mode.
            # Notes:
            # - Paragraphs can include multiple, trailing newlines, so that the
            #   client programs see the entire input text.
            # - Final newline is removed, as fed into process_line.
            # TODO: Have option to model perl-style paragraph mode more closely
            # with respect to handling more than 2 newlines between paragraphs; see
            #     https://perldoc.perl.org/variables/$/.
            else:
                new_paragraph = None
                if self.end_of_page:
                    new_paragraph = (line + "\n")
                    paragraph = ""
                elif ((last_line == "") and line):
                    new_paragraph = paragraph
                    paragraph = (line + "\n")
                else:
                    paragraph += (line + "\n")
                debug.trace_expr(7, new_paragraph, paragraph)
                if new_paragraph:
                    self.rel_para_num += 1
                    self.para_num += 1
                    debug.assertion(new_paragraph.endswith("\n\n") or (new_paragraph == "\n"))
                    if new_paragraph.endswith("\n"):
                        new_paragraph = new_paragraph[:-1]
                    self.process_line(new_paragraph)
            debug.assertion(not (self.track_pages and (not RETAIN_FORM_FEED) and (FORM_FEED in line)))
            last_line = line

        # Process the last set of lines if in paragraph mode
        # Note: Final newline is removed (as per process_line).
        if (self.paragraph_mode and paragraph):
            self.rel_para_num += 1
            self.para_num += 1
            debug.trace(5, "processing last paragraph")
            debug.assertion(paragraph.endswith("\n") or (paragraph == ""))
            if paragraph.endswith("\n"):
                paragraph = paragraph[:-1]
            self.process_line(paragraph)

        return

    def wrap_up(self) -> None:
        """Default end processing"""
        debug.trace_fmtd(5, "Main.wrap_up() stub: self={s}", s=self)
        return

    def clean_up(self) -> None:
        """Removes temporary files, etc."""
        # note: not intended to be overridden
        debug.trace_fmtd(5, "Main.clean_up(): self={s}", s=self)
        if not KEEP_TEMP_FILES:
            ## TODO2: 3=>6
            debug.trace_fmt(4, "Deleting any temporary files: {files}",
                            files=gh.run(f"echo {self.temp_base}* {self.temp_file}* | sort -u"))
                                
            # Remove all temp_base* files (or the temp_base directory)
            if self.use_temp_base_dir:
                ## OLD: gh.run("rm -rf {dir}", dir=self.temp_base)
                if DISABLE_RECURSIVE_DELETE:
                    debug.trace(4, f"FYI: Only deleting top-level files in {self.temp_base} to avoid potentially dangerous rm -r")
                    gh.run("rm -f {dir}/* {dir}/.*", dir=self.temp_base)
                    gh.run("rm -f {dir}", dir=self.temp_base)
                else:
                    debug.trace(4, f"FYI: Using potentially dangerous rm -r over {self.temp_base}")
                    gh.run("rm -rvf {dir}", dir=self.temp_base)
            else:
                gh.run("rm -vf {file}*", file=self.temp_base)
            # Likewise remove all temp_file* files
            if (self.temp_file != self.temp_base):
                gh.run("rm -vf {file}*", file=self.temp_file)
        return

#-------------------------------------------------------------------------------
# Global instance for convenient adhoc usage
# 
# note: useful for temporary file support (e.g., dummy_app.temp_file)
#

dummy_app = Main([])

debug.trace_current_context(8, "main.py context")

#------------------------------------------------------------------------

def main() -> None:
    """Entry point"""
    class VacuousMain(Main):
        """Sub-class that does nothing"""
        # Note: complexity is for handle python running script from shell-scripts repo
        #     run-python-sript"

        def run_main_step(self) -> None:
            print("No-op main step")
            
    # note: Following used for argument parsing
    ## OLD: main = Main(description=__doc__)
    ## NOTE: That hangs with run-python-script main.py
    main_app = VacuousMain(description=__doc__, skip_input=True, manual_input=True)
    ## TODO3: main.run_main_step = lambda self: print("No-op main step")
    main_app.run()


if __name__ == "__main__":
    system.print_stderr(f"Warning: {__file__} is not intended to be run standalone\n")
    main()
