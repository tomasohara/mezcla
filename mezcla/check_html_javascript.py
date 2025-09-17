#! /usr/bin/env python3
#
# Run embedded JavaScript from HTML page through code checking tools, such as
# jslint and jshint. This includes common definitions such as for DOM object
# (e.g., window) and JQuery ($ selector function). It also optionally runs
# in strict mode to help check other potential errors (e.g., undefined vars).
#
#

"""Run JavaScript embedded in <script> tags through lint-style code checkers

Usage example:
   {script} tests/resources/document_ready_test.html
"""

# Standard modules
from collections import defaultdict
import re
## OLD: import tempfile

# Local modules
# TODO: def tomas_import(name): ... components = eval(name).split(); ... import nameN-1.nameN as nameN
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla.my_regex import my_re
from mezcla import system

CODE_CHECKERS = "code-checkers"
STRIP_INDENT = "strip-indent"
SKIP_SAFE_MODE = "skip-safe-mode"
SKIP_COMMON_DEFINES = "skip-common-defines"
JAVASCRIPT_HEADER = "javascript-header"
#
## OLD:
## # TODO: put script-based temporary filename basename support into main
## DEFAULT_PREFIX = (system.remove_extension(__file__) or "check-js")
## TEMP_PREFIX = system.getenv_text("TEMP_PREFIX", DEFAULT_PREFIX,
##                                  "Temporary file prefix (see tempfile.mkstemp)")
## TEMP_SUFFIX = system.getenv_text("TEMP_SUFFIX", "-",
##                                  "Temporary file suffix (see tempfile.mkstemp)")
## # NOTE: see tempfile.mkstemp for NamedTemporaryFile keyword args
## DEFAULT_TEMP_BASE = tempfile.NamedTemporaryFile(prefix=TEMP_PREFIX, suffix=TEMP_SUFFIX).name
## TEMP_BASE = system.getenv_text("TEMP_BASE", DEFAULT_TEMP_BASE,
##                                "Basename with directory for temporary files")
#
MAX_ERRORS = system.getenv_int("MAX_ERRORS", 10000,
                               "Maxmium number of erros to report")
#
# note: see DEFAULT_JAVASCRIPT_HEADER below for other options
JSLINT = "jslint"
JSLINT_PROGRAM = system.getenv_text(
    "JSLINT_PROGRAM", JSLINT,
    desc="Script to invoke jslint")
JSLINT_OPTIONS = system.getenv_text(
    "JSLINT_OPTIONS", f"--maxerr {MAX_ERRORS} --white",
    desc="Options for jslint")
JSHINT = "jshint"
JSHINT_PROGRAM = system.getenv_text(
    "JSHINT_PROGRAM", JSHINT,
    desc="Script to invoke jshint")
JSHINT_OPTIONS = system.getenv_text(
    "JSHINT_OPTIONS", "--show-non-errors",
    desc="Options for jshint")
DEFAULT_CODE_CHECKERS = system.getenv_text(
    "CODE_CHECKERS",
    f"{JSLINT},  {JSHINT}",
    desc="JavaScript code checking commands")
SKIP_STRICT_MODE = system.getenv_bool(
    "SKIP_STRICT_MODE", False,
    desc="Whether to skip strict more: trumps command line args")
USE_STRICT_MODE = not SKIP_STRICT_MODE
SAFEMODE_HEADER = """
    // Added for sanity checking (e.g., undefined variables)
    "use strict";               // jshint ignore:line
""" if USE_STRICT_MODE else ""

# TODO: use separate headers for jslint and jshint
DEFAULT_JAVASCRIPT_HEADER = (f"""
    // note: silly need to work around inflexible parsers of both programs

    // Stuff for jslint:
          /*global $, jQuery, alert*/   // jshint ignore:line
    // Assume browser environment
          /*jslint browser*/            // jshint ignore:line
    // Allow console.log() and friends.
          /*jslint devel*/              // jshint ignore:line
    // Allow long lines.
          /*jslint long*/               // jshint ignore:line
    // Allow messy whitespace.
          /*jslint white*/              // jshint ignore:line

    // Stuff for jshint:
          /* jshint maxerr: {MAX_ERRORS} */
          /* jshint esversion: 6 */
"""
+ ("""
    // note: same as "use strict"
          /* jshint globalstrict: false */
          /* jshint strict: true */
""" if USE_STRICT_MODE else "")
+ """
    // Start of added header (JavaScript and jQuery definitions)
    // TEMP: includes workaround for silly jslint filters
    // TODO: make jQuery and bootstrap individually conditional
    var document;
    var window;
    var jQuery;
    var bootstrap;
    var console;
    function $(selector, context) { selector = context; }
    function trace () { return; }
    console.log = trace;
    console.debug = trace;

    // End of added header
""")
# TODO3: add pointer to definition (e.g., https://www.jslint.com)

class Script(Main):
    """Input processing class"""
    # TODO: -or-: """Adhoc script class (e.g., no I/O loop, just run calls)"""
    code_checkers = DEFAULT_CODE_CHECKERS
    strip_indent = False
    skip_safe_mode = False
    skip_common_defines = False
    javascript_header = DEFAULT_JAVASCRIPT_HEADER

    def __init__(self, *args, **kwargs):
        debug.trace_fmtd(5, "Script.__init__({a}): keywords={kw}; self={s}",
                         a=",".join(args), kw=kwargs, s=self)
        self.script_code = ""
        self.in_script = False
        self.code_indent = None
        super().__init__(*args, **kwargs)

    def setup(self):
        """Check results of command line processing"""
        debug.trace_fmtd(5, "Script.setup(): self={s}", s=self)
        self.code_checkers = self.get_parsed_option(CODE_CHECKERS, self.code_checkers)
        self.strip_indent = self.get_parsed_option(STRIP_INDENT, self.strip_indent)
        self.skip_safe_mode = self.get_parsed_option(SKIP_SAFE_MODE, self.skip_safe_mode)
        self.skip_common_defines = self.get_parsed_option(SKIP_COMMON_DEFINES, self.skip_common_defines)
        self.javascript_header = self.get_parsed_option(JAVASCRIPT_HEADER, self.javascript_header)
        debug.trace_object(5, self, label="Script instance")

    def process_line(self, line):
        """Processes current line from input"""
        # Notes: Issues warning when src attribute given along with bracketted code
        # Also, issues warning when bracketted code on same line as <script> tag.
        debug.trace_fmtd(6, "Script.process_line({l})", l=line)
        entire_line = line
        script_tag_count = 0

        # Check for start of code section, ignoring external script via src attribute
        # TODO2: exclude <script> in quoted text (e.g., 'console.log("in <script>");')
        while my_re.search(r"^([^<>]*)<\/?script[^<>]*>(.*)", line):
            remainder = my_re.group(2)
            if my_re.search(r"^\s*<script[^<>]*>(.*)$", line):
                debug.assertion(not self.in_script)
                self.in_script = True
                line = my_re.group(1)
                script_tag_count += 1
            elif my_re.search(r"^(.*)</script[^<>]*>(.*)", line):
                debug.assertion(self.in_script)
                code = my_re.group(1).strip()
                line = my_re.group(2)
                self.in_script = False
                if code:
                    self.script_code += code + "\n"
            else:
                system.print_stderr("Warning: ignoring unexpected script tag formatting at line {n}: {t}", n=self.line_num, t=entire_line)
                line = remainder
        debug.assertion(script_tag_count <= 1)
        if script_tag_count:
            debug.trace_fmt(4, "{n} <script> taggings: in_script={ins}", n=script_tag_count, ins=self.in_script)

        # Accumulate text if within script tags
        if self.in_script:
            # Make sure indentation is defined if being stripped
            # Note: All code is stripped of indentation, so that aligns with javascript header.
            # This is just determined by first non-blank line, so that if-blocks, etc. not stripped of all spacing.
            if (self.strip_indent and line.strip()):
                # Make sure indentation defined
                if (self.code_indent is None):
                    self.code_indent = ""
                    if my_re.search(r"^(\s+)(.*)", line):
                        self.code_indent = my_re.group(1)
                        line = my_re.group(2)
                        debug.assertion(len(self.code_indent) > 0)
                    debug.trace_fmt(4, "Indent to strip: '{ind}' (len={l})", ind=self.code_indent, l=len(self.code_indent))
                # Strip indentation from start of line
                line = line.replace(self.code_indent, "", 1)
            #
            self.script_code += line.rstrip() + "\n"

    def wrap_up(self):
        """Run the accumulated script through code checkers"""
        debug.trace(5, "Script.wrap_up()")
        debug.trace_expr(5, self.script_code)
        if (not self.script_code.strip()):
            system.print_stderr("Error: No code found within <script> tags")
        ## OLD: javascript_file = (TEMP_BASE + ".js")
        javascript_file = (gh.get_temp_file() + ".js")

        # Add in header for strict mode (optional) and a few JavaScript defines
        code_header = ""
        if not self.skip_safe_mode:
            code_header += SAFEMODE_HEADER
        if not self.skip_common_defines:
            code_header += self.javascript_header
        system.write_file(javascript_file, code_header + self.script_code)
        output = None
        default_options_hash = defaultdict(str)
        default_options_hash.update({JSLINT: JSLINT_OPTIONS,
                                     JSHINT: JSHINT_OPTIONS})
        default_program_hash = defaultdict(str)
        default_program_hash.update({JSLINT: JSLINT_PROGRAM,
                                     JSHINT: JSHINT_PROGRAM})
        for checker in re.split(", *", self.code_checkers):
            if output is not None:
                print("-" * 80)
            ## TODO3: clarify why options being re-initialized
            options_var = f"{checker}_OPTIONS".upper()
            checker_options = system.getenv_text(
                options_var, default_options_hash[checker],
                skip_register=True)
            program_var = f"{checker}_PROGRAM".upper()
            checker_program = system.getenv_text(
                program_var, default_program_hash[checker],
                skip_register=True)
            output = gh.run("{ch} {opt} {scr}",
                            ch=checker_program, opt=checker_options, scr=javascript_file)
            print("Output from {ch}:".format(ch=checker))
            print(output)
            print("")

            
def main():
    """Entry point"""
    app = Script(
        description=__doc__.format(script=gh.basename(__file__)),
        # Note: skip_input controls the line-by-line processing, which is inefficient but simple to
        # understand; in contrast, manual_input controls iterator-based input (the opposite of both).
        skip_input=False,
        manual_input=False,
        # TODO: skip_input=True,
        # TODO: manual_input=True,
        boolean_options=[STRIP_INDENT, SKIP_SAFE_MODE, SKIP_COMMON_DEFINES],
        text_options=[
            (CODE_CHECKERS, "Comma-separated list of code checking invocations (e.g., '{dfc}')".format(dfc=DEFAULT_CODE_CHECKERS)),
            (JAVASCRIPT_HEADER, "JavaScript header with common definitions (e.g., document, window, jQuery)")])
    app.run()
       
#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    debug.trace_current_context(level=debug.QUITE_DETAILED)
    main()
