#! /usr/bin/env python3
#
# Utility functions for writing glue scripts, such as implementing functionality
# available in Unix scripting (e.g., basename command).
#
# NOTE:
# - Some of the utilities are specific to Unix (e.g., full_mkdir and real_path). In
#   contrast, system.py attempts to be more cross platform.
# - ** It can be confusing debugging script that use run, because the trace level
#  is raised by default. To disable this, set the SUB_DEBUG_LEVEL as follows:
#     l=5; DEBUG_LEVEL=$l SUB_DEBUG_LEVEL=$l merge_files.py ...
# - Also see ALLOW_SUBCOMMAND_TRACING usage below and in unittest_wrapper.py.
# - By default, temporary files are created in the system temporary directory. To
#   facilate debugging, two environment variables allow for overriding this
#      TEMP_FILE: fixed temporary file to use (** avoid if possible)
#      TEMP_BASE: basename for temporary files (or a directory if USE_TEMP_BASE_DIR)
# - Uses str as return type instead of Optional[str] for string functions like basename
#   or get_temp_dir where "" is an invalid value (e.g., no need for None).
# - Avoids adding assert for mypy unless trapped.
#
# TODO:
# - Add more functions to facilitate command-line scripting (check bash scripts for commonly used features).
# - Add functions to facilitate functional programming (e.g., to simply debugging traces).
# TODO3: add deprecated warnings to functions superceded by ones in system
#

"""Helpers gluing scripts together

Usage example:

   cat {script} | python -c 'from mezcla import glue_helpers, system; print("\\n".join(glue_helpers.elide_values(system.read_lines("{script}"))))'
"""

# Standard packages
from collections import defaultdict
import glob
import inspect
import os
from pathlib import Path
import re
import shutil
from subprocess import getoutput
import sys
import tempfile
from typing import (
    Optional, Any, List, Dict, Union,
    ## OLD: TextIO,
)
from types import FrameType
## OLD: from io import TextIOWrapper
## DEBUG: sys.stderr.write(f"{__file__=}\n")

# Installed packages
import textwrap

# Local packages
from mezcla import debug
from mezcla import system
from mezcla.tpo_common import format as tpo_format
## TODO3: debug.trace_expr(6, __file__)
from mezcla.validate_arguments_types import (
    FileDescriptorOrPath, StrOrBytesPath
)

# Constants
TL = debug.TL

# Environment options
#
# note:
# - ALLOW_SUBCOMMAND_TRACING should be interepreted in terms of detailed
# tracing. Now, basic tracing is still done unless disable_subcommand_tracing()
# invoked. (This way, the subscript start/end time is still shown by default)
# - SUB_DEBUG_LEVEL added to make sub-script trace level explicit
DEFAULT_SUB_DEBUG_LEVEL = int(min(debug.TL.USUAL, debug.get_level()))
SUB_DEBUG_LEVEL = system.getenv_int(
    "SUB_DEBUG_LEVEL", DEFAULT_SUB_DEBUG_LEVEL,
    description="Tracing level for sub-command scripts invoked")
default_subtrace_level = SUB_DEBUG_LEVEL
ALLOW_SUBCOMMAND_TRACING = system.getenv_boolean(
    "ALLOW_SUBCOMMAND_TRACING",
    (SUB_DEBUG_LEVEL > DEFAULT_SUB_DEBUG_LEVEL),
    description="Whether sub-commands have tracing above TL.USUAL")
if ALLOW_SUBCOMMAND_TRACING:
    # TODO: work out intuitive default if both SUB_DEBUG_LEVEL and ALLOW_SUBCOMMAND_TRACING specified
    default_subtrace_level = max(debug.get_level(), SUB_DEBUG_LEVEL)

INDENT = system.getenv_text(
    "INDENT_TEXT", "    ",
    description="Default indentation")
# 
# note: See main.py for similar support as part of Main scipt class
FILE_BASE = system.getenv_text(
    "FILE_BASE", "_temp",
    description="Basename for output files including dir")
TEMP_PREFIX = system.getenv_text(
    "TEMP_PREFIX", FILE_BASE + "-",
    description="Prefix to use for temp files")
TEMP_SUFFIX = system.getenv_text(
    "TEMP_SUFFIX", "_",
    description="Suffix to use for temp files")
KEEP_TEMP = system.getenv_bool(
    "KEEP_TEMP", debug.detailed_debugging(),
    desc="Keep temporary files")
TEMP_BASE = system.getenv_value(
    "TEMP_BASE", None,
    description="Debugging override for temporary file basename")
USE_TEMP_BASE_DIR_DEFAULT = bool(
    TEMP_BASE and (system.is_directory(TEMP_BASE) or TEMP_BASE.endswith("/")))
USE_TEMP_BASE_DIR = system.getenv_bool(
    "USE_TEMP_BASE_DIR", USE_TEMP_BASE_DIR_DEFAULT,
    description="Whether TEMP_BASE should be a dir instead of prefix")
DISABLE_RECURSIVE_DELETE = system.getenv_value(
    "DISABLE_RECURSIVE_DELETE", debug.detailed_debugging(),
    description="Disable potentially dangerous rm -r style or rmtree recursive deletions")
PRESERVE_TEMP_FILE = None
HOME_DIR = system.getenv_text(
    "HOME", Path.home(),
    description="User home directory")

# Globals
# note:
# - see init() for main initialization;
#   these are placeholders until module initialized below (see init)
# - os.path.join used to likewise avoid chicken-n-egg problems with init
# - TEMP_FILE is normally None to indicate use of random temp file name
# - TEMP_LOG_FILE and TEMP_SCRIPT_FILE are used in run, issue, etc.
# TODO3: make GLOBAL_TEMP_FILE, etc. lowercase
TMP = system.getenv_text(
    "TMP", "/tmp",
    description="Temporary directory")
PID = system.get_process_id()
TEMP_FILE = None
PID_BASENAME = f"temp-{PID}"
GLOBAL_TEMP_FILE = os.path.join(TMP, PID_BASENAME)
TEMP_LOG_FILE = os.path.join(TMP, f"{GLOBAL_TEMP_FILE}.log")
TEMP_SCRIPT_FILE = os.path.join(TMP, f"{GLOBAL_TEMP_FILE}.script")
initialized = False

#------------------------------------------------------------------------

def get_temp_file(delete: Optional[bool] = None) -> str:
    """Return name of unique temporary file, optionally with DELETE"""
    # Note: delete defaults to False if detailed debugging
    # TODO: allow for overriding other options to NamedTemporaryFile
    if ((delete is None) and not KEEP_TEMP):
        delete = False
    NTF_ARGS = {'prefix': TEMP_PREFIX,
                'delete': delete,
                'suffix': TEMP_SUFFIX}
    temp_file_name = TEMP_FILE
    if not temp_file_name:
        # note: uses context so not deleted right away if delete=True
        # TODO2: fix this
        with tempfile.NamedTemporaryFile(**NTF_ARGS) as temp_file_obj:
            temp_file_name = temp_file_obj.name
        # HACK: clear the file
        if not KEEP_TEMP:
            system.write_file(temp_file_name, "")
    ## TODO2: drop ... or ""
    temp_file_name = temp_file_name or ""
    debug.assertion(not delete, "Support for delete not implemented")
    debug.trace_fmtd(5, "gh.get_temp_file() => {r!r}", r=temp_file_name)
    return temp_file_name


def get_temp_dir(delete=None) -> str:
    """Gets temporary file to use as a directory
    note: Optionally DELETEs directory afterwards
    """
    ## TODO3: make option to bypass creation
    temp_dir_path = get_temp_file(delete=delete)
    # note: removes non-dir file if exists
    full_mkdir(temp_dir_path, force=True)
    debug.trace_fmtd(5, "gh.get_temp_dir() => {r!r}", r=temp_dir_path)
    return temp_dir_path


def create_temp_file(contents: Any, binary: bool = False) -> str:
    """Create temporary file with CONTENTS and return full path"""
    temp_filename = get_temp_file()
    system.write_file(temp_filename, contents, binary=binary)
    debug.trace(6, f"create_temp_file({contents!r}) => {temp_filename}")
    return temp_filename


def basename(filename: str, extension: Optional[str] = None) -> str:
    """Remove directory from FILENAME along with optional EXTENSION, as with Unix basename command. Note: the period in the extension must be explicitly supplied (e.g., '.data' not 'data')"""
    # EX: basename("fubar.py", ".py") => "fubar"
    # EX: basename("fubar.py", "py") => "fubar."
    # EX: basename("/tmp/solr-4888.log", ".log") => "solr-4888"
    base = os.path.basename(filename) or ""
    if extension is not None:
        pos = base.find(extension)
        if pos > -1:
            base = base[:pos]
    debug.trace(5, f"basename({filename!r}, {extension}) => {base}")
    return base


def remove_extension(filename: str, extension: str) -> str:
    """Returns FILENAME without EXTENSION. Note: similar to basename() but retaining directory portion."""
    # EX: remove_extension("/tmp/solr-4888.log", ".log") => "/tmp/solr-4888"
    # EX: remove_extension("/tmp/fubar.py", ".py") => "/tmp/fubar"
    # EX: remove_extension("/tmp/fubar.py", "py") => "/tmp/fubar."
    # NOTE: Unlike os.path.splitext, only the specific extension is removed (not whichever extension used).
    pos = filename.find(extension)
    base = filename[:pos] if (pos > -1) else filename
    debug.trace(5, f"remove_extension({filename!r}, {extension}) => {base!r}")
    return base


## TODO: def replace_extension(filename, old_extension, old_extension):
##           ...


def dir_path(filename: str, explicit: bool = False) -> str:
    """Wrapper around os.path.dirname over FILENAME
    Note: With EXPLICIT, returns . instead of "" (e.g., if filename in current directory)
    """
    # TODO: return . for filename without directory (not "")
    # EX: dir_path("/tmp/solr-4888.log") => "/tmp"
    # EX: dir_path("README.md") => ""
    path = os.path.dirname(filename)
    if (not path and explicit):
        path = "."
    debug.trace(5, f"dir_path({filename!r}, [explicit={explicit}]) => {path}")
    # TODO: add realpath (i.e., canonical path)
    if not explicit:
        base = basename(filename)
        debug.assertion(form_path(path, base) == filename)
    return path


def dirname(file_path: str) -> str:
    """"Returns directory component of FILE_PATH as with Unix dirname
    Note: Unlike dir_path, this always returns explicit directory
    """
    # EX: dirname("/tmp/solr-4888.log") => "/tmp"
    # EX: dirname("README.md") => "."
    return dir_path(file_path, explicit=True)


def file_exists(filename: FileDescriptorOrPath) -> bool:
    """Returns indication that FILENAME exists"""
    ok = os.path.exists(filename)
    debug.trace(7, f"file_exists({filename!r}) => {ok}")
    return ok


def non_empty_file(filename: FileDescriptorOrPath) -> bool:
    """Whether FILENAME exists and is non-empty"""
    size = (os.path.getsize(filename) if os.path.exists(filename) else -1)
    non_empty = (size > 0)
    debug.trace(5, f"non_empty_file({filename!r}) => {non_empty}; (filesize={size})")
    return non_empty


def resolve_path(
        filename: str,
        base_dir: Optional[str] = None,
        heuristic: bool = False,
        absolute: bool = False,
    ) -> str:
    """Resolves path for FILENAME or path, relative to BASE_DIR if not in current directory. 
    Note:
    - This uses the script directory for the calling module if BASE_DIR not specified
      (e.g., as if os.path.dirname(__file__) passed).
    - If HEURISTIC, then also checks nearby directories such as parent for BASE_DIR, which
      is useful for resolving resources for tests, which normally run of module dir 
      (e.g., mezcla for mezcla/tests/test_template.py): see test_heuristic_resolve_path.
    - HEURISTIC also uses find.
    - If ABSOLUTE, then the full path is returned.
    """
    ## TODO4: rename filename to sub_path for clarity
    debug.trace(5, f"in resolve_path({filename!r})")
    debug.trace_expr(6,  base_dir, heuristic)
    # TODO: give preference to script directory over current directory
    path = filename
    if not os.path.exists(path):
        # Determine directly for calling module
        if not base_dir:
            frame = None
            try:
                frame = inspect.currentframe()
                assert isinstance(frame, FrameType)
                frame = frame.f_back
                assert isinstance(frame, FrameType)
                calling_filename = frame.f_globals['__file__']
                base_dir = os.path.dirname(calling_filename)
                debug.trace_expr(4, calling_filename, base_dir)
            except (AssertionError, AttributeError, KeyError):
                base_dir = ""
                debug.trace(5, "Error: Exception during resolve_path: " + str(sys.exc_info()))
            finally:
                if frame:
                    del frame
        if not isinstance(base_dir, str):
            base_dir = str(base_dir)
        
        # Check calling directory (TODO2: add more check dirs such as children)
        dirs_to_check = [base_dir]
        if heuristic:
            dirs_to_check += [form_path(base_dir, ".."), form_path(".", "..")]
        for check_dir in dirs_to_check:
            check_path = os.path.join(check_dir, path)
            if os.path.exists(check_path):
                path = check_path
                break
    # Fall back to using find command
    if (not os.path.exists(path)) and heuristic:
        debug.trace(4, f"FYI: resolve_path falling back to find for {path!r}")
        debug.assertion(" " not in path)
        debug.assertion(base_dir)
        path = run(f"find {base_dir or '.'} -name '{path}'")

    # Make sure full path if desired
    if absolute:
        path = system.absolute_path(path)
            
    debug.trace_fmtd(4, "resolve_path({f}) => {p}", f=filename, p=path)
    return path


def form_path(*filenames: str, create: bool = False) -> str:
    """Wrapper around os.path.join over FILENAMEs (with tracing)
    Note: includes sanity check about absolute filenames except for first
    If CREATE, then the directory for the path is created if needed
    Warning: This might be deprecated: use system.form_path instead.
    """
    debug.assertion(not any(f.startswith(system.path_separator()) for f in filenames[1:]))
    if create:
        ## TODO2: add dir option so that all filenames used for path
        path_dir = os.path.join(*filenames[:-1])
        if not system.file_exists(path_dir):
            full_mkdir(path_dir)

    path = os.path.join(*filenames)
    debug.trace(6, f"form_path({filenames}, [create={create}]) => {path}")
    return path


def is_directory(path: FileDescriptorOrPath) -> bool:
    """Determines whether PATH represents a directory"""
    is_dir = os.path.isdir(path)
    debug.trace_fmtd(6, "is_dir({p}) => {r}", p=path, r=is_dir)
    return is_dir


## TODO2: add decorator for flagging obsolete functions
##   def obsolete():
##      """Flag fucntion as obsolete in docstring and issue warning if called"""
##      warning = f"Warning {func} obsolete use version in system.py instead"
##      func.docstring += warning
##      func.body = f'debug.trace(3, "{warning}")' + func.body


def create_directory(path: StrOrBytesPath) -> None:
    """Wrapper around os.mkdir over PATH (with tracing)
    Warning: obsolete
    """
    debug.trace(3, "Warning: create_directory obsolete use version in system.py instead")
    system.create_directory(path)
    return


def full_mkdir(path: FileDescriptorOrPath, force: bool = False) -> FileDescriptorOrPath:
    """Issues mkdir to ensure path directory, including parents (assuming Linux like shell)
    Note:
    - When FORCE true, an existing non-directory is removed first.
    - Otherwise, doesn't handle case when file exists but is not a directory.
    - Returns path, which is useful for temporary sub-directory creation:
    -   gh.full_mkdir(gh.form_path(gh.get_temp_dir(), 'my_temp_subdir'))
    """
    debug.trace(6, f"full_mkdir({path!r})")
    debug.assertion(os.name == "posix")
    if force and system.file_exists(path) and not system.is_directory(path):
        delete_file(path)
    if not system.file_exists(path):
        os.makedirs(path, exist_ok=True)
    debug.assertion(is_directory(path))
    return path


def real_path(path: FileDescriptorOrPath) -> str:
    """Return resolved absolute pathname for PATH, as with Linux realpath command
    Note: Use version in system instead"""
    # EX: re.search("vmlinuz.*\d.\d", real_path("/vmlinuz"))
    ## TODO: result = system.real_path(path)
    ## TODO3: check outher modules for over-applicaiton of !r-formatting
    ## BAD: result = run(f'realpath "{path!r}"')
    result = run(f'realpath "{path}"')
    debug.trace(6, "Warning: obsolete: use system.real_path instead")
    debug.trace(7, f"real_path({path!r}) => {result}")
    return result


def indent(text: str, indentation: Optional[str] = None, max_width: int = 512) -> str:
    """Indent TEXT with INDENTATION at beginning of each line, returning string ending in a newline unless empty and with resulting lines longer than max_width characters wrapped. Text is treated as a single paragraph."""
    if indentation is None:
        indentation = INDENT
    # Note: an empty text is returned without trailing newline
    tw = textwrap.TextWrapper(width=max_width, initial_indent=indentation, subsequent_indent=indentation)
    wrapped_text = "\n".join(tw.wrap(text))
    if wrapped_text and text.endswith("\n"):
        wrapped_text += "\n"
    return wrapped_text


def indent_lines(text: str, indentation: Optional[str] = None, max_width: int = 512) -> str:
    """Like indent, except that each line is indented separately. That is, the text is not treated as a single paragraph."""
    # Sample usage: print("log contents: {{\n{log}\n}}".format(log=indent_lines(lines)))
    # TODO: add support to simplify above idiom (e.g., indent_lines_bracketed); rename to avoid possible confusion that input is array (as wih write_lines)
    if indentation is None:
        indentation = INDENT
    result = ""
    for line in text.splitlines():
        indented_line = indent(line + "\n", indentation, max_width)
        if not indented_line:
            indented_line = "\n"
        result += indented_line
    return result


MAX_ELIDED_TEXT_LEN = system.getenv_integer("MAX_ELIDED_TEXT_LEN", 128)
#
def elide(value: Optional[Any], max_len: Optional[int] = None) -> str:
    """Returns VALUE converted to text and elided to at most MAX_LEN characters (with '...' used to indicate remainder). 
    Note: intended for tracing long strings."""
    # EX: elide("=" * 80, max_len=8) => "========..."
    # EX: elide(None) => ""
    # NOTE: Make sure compatible with debug.format_value (TODO3: add equivalent to strict argument)
    # TODO2: add support for eliding at word-boundaries
    debug.trace(8, "elide(_, _)")
    text = value
    if text is None:
        text = ""
    if (not isinstance(text, str)):
        text = str(text)
    if max_len is None:
        max_len = MAX_ELIDED_TEXT_LEN
    result = text
    if (result and (len(result) > max_len)):
        result = result[:max_len] + "..."
    debug.trace(9, "elide({%s}, [{%s}]) => {%s}" % (text, max_len, result))
    return result
#
# EX: elide(None, 10) => ''

def elide_values(values: List[Any], **kwargs) -> List[str]:
    """List version of elide [q.v.]"""
    # EX: elide_values(["1", "22", "333"], max_len=2) => ["1", "22", "33..."]
    debug.trace(7, "elide_values(_, _)")
    return list(map(lambda v: elide(str(v), **kwargs),
                    values))


def disable_subcommand_tracing() -> None:
    """Disables tracing in scripts invoked via run().
    Note: Invoked in unittest_wrapper.py"""
    debug.trace(7, "disable_subcommand_tracing()")
    # Note this works by having run() temporarily setting DEBUG_LEVEL to 0."""
    global default_subtrace_level
    default_subtrace_level = 0


def run(
        command: str,
        trace_level: debug.IntOrTraceLevel = 4,
        subtrace_level: Optional[debug.IntOrTraceLevel] = None,
        just_issue: Optional[bool] = None,
        output: bool = False,
        **namespace
    ) -> str:
    """Invokes COMMAND via system shell (e.g., os.system), using TRACE_LEVEL for debugging output, returning result. The command can use format-style templates, resolved from caller's namespace. The optional SUBTRACE_LEVEL sets tracing for invoked commands (default is same as TRACE_LEVEL); this works around problem with stderr not being separated, which can be a problem when tracing unit tests.
   Notes:
   - The result includes stderr, so direct if not desired (see issue):
         run("ls /tmp/fubar 2> /dev/null")
   - This is only intended for running simple commands. It would be better to create a subprocess for any complex interactions.
   - This function doesn't work fully under Win32. Tabs are not preserved, so redirect stdout to a file if needed.
   - If TEMP_FILE or TEMP_BASE defined, these are modified to be unique to avoid conflicts across processeses.
    - If OUTPUT, the result will be printed.
   """
    # TODO: add automatic log file support as in run_script from unittest_wrapper.py
    # TODO: make sure no template markers left in command text (e.g., "tar cvfz {tar_file}")
    # EX: "root" in run("ls /")
    # Note: Script tracing controlled DEBUG_LEVEL environment variable.
    debug.assertion(isinstance(trace_level, int))
    debug.trace(trace_level + 2, f"run({command}, tl={trace_level}, sub_tr={subtrace_level}, iss={just_issue}, out={output})", skip_sanity_checks=True)
    global default_subtrace_level
    # Keep track of current debug level settings for later restoration
    debug_level_env = os.getenv("DEBUG_LEVEL")
    sub_debug_level_env = os.getenv("SUB_DEBUG_LEVEL")
    if subtrace_level is None:
        subtrace_level = default_subtrace_level
    if subtrace_level != system.to_int(debug_level_env, ignore=True):
        system.setenv("DEBUG_LEVEL", str(subtrace_level))
    if subtrace_level != system.to_int(sub_debug_level_env, ignore=True):
        # note: for run/issue called within scripts
        system.setenv("SUB_DEBUG_LEVEL", str(subtrace_level))
    in_just_issue = just_issue
    if just_issue is None:
        just_issue = False
    save_temp_base = TEMP_BASE
    if TEMP_BASE:
        # note: makes sure subprocess TEMP_BASE is dir if main one is
        if system.is_directory(TEMP_BASE) or TEMP_BASE.endswith("/"):
            system.create_directory(TEMP_BASE)
            new_TEMP_BASE = form_path(TEMP_BASE, "_subprocess_", create=True)
            system.setenv("TEMP_BASE", new_TEMP_BASE)
            ## TEMP
            system.create_directory(new_TEMP_BASE)
        else:
            system.setenv("TEMP_BASE", TEMP_BASE + "_subprocess_")
    save_temp_file = TEMP_FILE
    if TEMP_FILE and (PRESERVE_TEMP_FILE is not True):
        new_TEMP_FILE = TEMP_FILE + "_subprocess_"
        debug.trace_expr(5, PRESERVE_TEMP_FILE)
        debug.trace(5, f"Setting TEMP_FILE to {new_TEMP_FILE}")
        system.setenv("TEMP_FILE", new_TEMP_FILE)
    # Expand the command template if brace-style variable reference encountered
    # NOTE: un-pythonic warnings issued by format so this should not affect anything
    # TODO: make this optional
    command_line = command
    if (re.search(r"{\S+}", command) or namespace):
        if not namespace:
            ## TODO3: weed out gh.run calls with empty kwargs
            debug.trace(4, "Warning: deprecated interpolation used for gh.run")
        command_line = tpo_format(command_line, indirect_caller=True, ignore_exception=False, **namespace)
    else:
        # TODO2: and sanity check for unresolved f-string-like template as with debug.trace
        pass
    debug.trace(trace_level, "issuing: %s" % command_line)
    # Run the command
    # TODO: check for errors (e.g., "sh: filter_file.py: not found"); make wait explicit
    in_background = command.strip().endswith("&")
    foreground_wait = not in_background
    debug.trace_expr(5, in_background, in_just_issue)
    debug.assertion(not (in_background and (in_just_issue is False)))
    # Note: Unix supports the '>|' pipe operator (i.e., output with overwrite); but,
    # it is not supported under Windows. To avoid unexpected porting issues, clients
    # should replace 'run("... >| f")' usages with 'delete_file(f); run(...)'.
    # note: TestWrapper.setUp handles the deletion automatically
    debug.assertion(">|" not in command_line)
    result = None
    ## TODO: if (just_issue or not foreground_wait): ... else: ...
    wait_for_command = (foreground_wait and not just_issue)
    debug.trace_expr(5, foreground_wait, just_issue, wait_for_command)
    ## TODO3: clarify what output is when stdout redirected (e.g., for issue in support of unittest_wrapper.run_script
    result = getoutput(command_line) if wait_for_command else str(os.system(command_line))
    if output:
        print(result)
    # Restore debug level setting in environment
    system.setenv("DEBUG_LEVEL", debug_level_env or "")
    system.setenv("SUB_DEBUG_LEVEL", sub_debug_level_env or "")
    system.setenv("TEMP_BASE", save_temp_base or "")
    if save_temp_file and (PRESERVE_TEMP_FILE is not True):
        debug.trace(5, f"Resetting TEMP_FILE to {save_temp_file}")
        system.setenv("TEMP_FILE", save_temp_file)
    debug.trace_fmt((trace_level + 1), "run(_) => {{\n{r}\n}}", r=indent_lines(result))
    return result


def run_via_bash(
        command: str,
        trace_level: debug.IntOrTraceLevel = 4,
        subtrace_level: Optional[debug.IntOrTraceLevel] = None,
        init_file: Optional[bool] = None,
        enable_aliases: bool = False,
        **namespace
    ) -> str:
    """Version of run that runs COMMAND with aliases defined
    Notes:
    - This can be slow due to alias definition overhead
    - INIT_FILE is file to source before running the command
    - TRACE_LEVEL and SUBTRACE_LEVEL control tracing for COMMAND and any subcommands, respectively
    - Used in bash to python translation; see
         https://github.com/tomasohara/shell-scripts/blob/main/bash2python.py
    """
    debug.trace(trace_level, "issuing: %s" % command)
    commands_to_run = ""
    if enable_aliases:
        commands_to_run += "shopt -s expand_aliases\n"
    if init_file:
        commands_to_run += system.read_file(init_file) + "\n"
    commands_to_run += command
    system.write_file(TEMP_SCRIPT_FILE, commands_to_run)
    
    command_line = f"bash -f {TEMP_SCRIPT_FILE}"
    return run(command_line, trace_level=(trace_level + 1), subtrace_level=subtrace_level, just_issue=False, **namespace)


def issue(
        command: str,
        trace_level: debug.IntOrTraceLevel = 4,
        subtrace_level: Optional[debug.IntOrTraceLevel] = None,
        log_file: Optional[str] = None,
        **namespace
    ) -> None:
    """Wrapper around run() for when output is not being saved (i.e., just issues command). 
    Note:
    - Nothing is returned.
    - Traces stdout when debugging at quite-detailed level (6).
    - Captures stderr unless redirected and traces at error level (1)."""
    # EX: issue("ls /") => None
    # EX: issue("xeyes &")
    debug.trace_fmt(
        (trace_level + 1), "issue({c}, [trace_level={tl}], [sub_level={sl}], [ns={n}])",
        c=command, tl=trace_level, sl=subtrace_level, n=namespace)
    # Add stderr redirect to temporary log file, unless redirection already present
    log_file = None
    has_stderr_redir = ("2>" in command) or ("2|&1" in command)
    if (not log_file) and debug.debugging() and (not has_stderr_redir):
        ## TODO: use a different suffix each time to aid in debugging
        log_file = TEMP_LOG_FILE
    if log_file:
        debug.assertion(not has_stderr_redir)
        delete_existing_file(log_file)
        command += " 2> " + log_file
    # Run the command and trace output
    command_line = command
    if re.search("{.*}", command_line):
        if not namespace:
            ## TODO3: weed out gh.issue calls with empty kwargs
            debug.trace(4, "Warning: deprecated interpolation used for gh.issue")
        command_line = tpo_format(command_line, indirect_caller=True, ignore_exception=False, **namespace)
    output = run(command_line, trace_level, subtrace_level, just_issue=True)
    debug.trace((2 + trace_level), "stdout from command: {\n%s\n}\n" % indent(output))
    # Trace out any standard error output and remove temporary log file (unless debugging)
    if log_file:
        if debug.debugging() and non_empty_file(log_file):
            stderr_output = indent(read_file(log_file))
            debug.trace(1, "stderr output from command: {\n%s\n}\n" % indent(stderr_output))
        if not debug.detailed_debugging():
            ## TODO4: add option for deletion
            delete_file(log_file)
    return


def get_hex_dump(text: Any, break_newlines: bool = False) -> str:
    """Get hex dump for TEXT, optionally BREAKing lines on NEWLINES"""
    # TODO: implement entirely within Pyton (e.g., via binascii.hexlify)
    # EX: get_hex_dump("Tomás") => \
    #   "00000000  54 6F 6D C3 A1 73       -                          Tom..s"
    debug.trace_fmt(6, "get_hex_dump({t}, {bn})", t=text, bn=break_newlines)
    in_file = get_temp_file() + ".in.list"
    out_file = get_temp_file() + ".out.list"
    system.write_file(in_file, text, skip_newline=True)
    run("perl -Ss hexview.perl {i} > {o}", i=in_file, o=out_file)
    result = read_file(out_file).rstrip("\n")
    debug.trace(7, f"get_hex_dump() => {result}")
    return result


def extract_matches(
        pattern: str,
        lines: List[str],
        fields: int = 1,
        multiple: bool = False,
        re_flags: int = 0,
        para_mode: Optional[bool] = False
    ) -> List[str]:
    """Checks for PATTERN matches in LINES of text returning list of tuples with replacement groups.
    Notes: The number of FIELDS can be greater than 1.
    Optionally allows for MULTIPLE matches within a line.
    The lines are concatenated if DOTALL
    Matching optionally uses perl-style PARA_MODE
    """
    ## TODO: If unspecified, the regex flags default to DOTALL.
    # ex: extract_matches(r"^(\S+) \S+", ["John D.", "Jane D.", "Plato"]) => ["John", "Jane"]
    # Note: modelled after extract_matches.perl
    # TODO: make multiple the default
    debug.trace(6, "extract_matches(%s, _, [fld=%s], [m=%s], [flg=%s], [para=%s])" % (pattern, fields, multiple, re_flags, para_mode))
    ## TODO
    ## if re_flags is None:
    ##     re_flags = re.DOTALL
    debug.trace_values(6, lines, "lines")
    debug.assertion(isinstance(lines, list))
    if pattern.find("(") == -1:
        pattern = "(" + pattern + ")"
    if (re_flags and (re_flags & re.DOTALL)):
        lines = [ "\n".join(lines) + "\n" ]
        debug.trace_expr(6, lines)
    if para_mode:
        lines = re.split(r"\n\s*\n", ("\n".join(lines)))
    matches = []
    for i, line in enumerate(lines):
        while line:
            debug.trace(6, f"L{i}: {line}")
            try:
                # Extract match field(s)
                debug.trace_expr(7, pattern, line, re_flags, fields)
                match = re.search(pattern, line, flags=re_flags)
                if not match:
                    break
                result = match.group(1) if (fields == 1) else [match.group(i + 1) for i in range(fields)]
                matches.append(result)
                if not multiple:
                    break

                # Revise line
                debug.assertion(match.end() > 0)
                new_line = line[match.end():]
                if (new_line == line):
                    break
                line = new_line
            except (re.error, IndexError):
                debug.trace(2, "Warning: Exception in pattern matching: %s" % str(sys.exc_info()))
                line = ""
    debug.trace(7, "extract_matches() => %s" % (matches))
    double_indent = INDENT + INDENT
    debug.trace_fmtd(8, "{ind}input lines: {{\n{res}\n{ind}}}",
                 ind=INDENT, res=indent_lines("\n".join(lines), double_indent))
    return matches


def extract_match(
        pattern: str,
        lines: List[str],
        fields: int = 1,
        multiple: bool = False,
        re_flags: int = 0,
        para_mode: Optional[bool] = None
    ):
    """Extracts first match of PATTERN in LINES for FIELDS"""
    matches = extract_matches(pattern, lines, fields, multiple, re_flags, para_mode)
    result = (matches[0] if matches else None)
    debug.trace(5, "match: %s" % result)
    return result


def extract_match_from_text(
        pattern: str,
        text: str,
        fields: int = 1,
        multiple: bool = False,
        re_flags: int = 0,
        para_mode: Optional[bool] = None
    ) -> Optional[str]:
    """Wrapper around extract_match for text input"""
    ## TODO: rework to allow for multiple-line matching
    return extract_match(pattern, text.split("\n"), fields, multiple, re_flags, para_mode)


def extract_matches_from_text(
        pattern: str,
        text: str,
        fields: int = 1,
        multiple: Optional[bool] = None,
        re_flags: int = 0,
        para_mode: Optional[bool] = None
    ) -> List[str]:
    """Wrapper around extract_matches for text input
    Note: By default MULTIPLE matches are returned"""
    # EX: extract_matches_from_text(".", "abc") => ["a", "b", "c"]
    # EX: extract_matches_from_text(".", "abc", multiple=False) => ["a"]
    if multiple is None:
        multiple = True
    # TODO: make multiple True by default
    return extract_matches(pattern, text.split("\n"), fields, multiple, re_flags, para_mode)


def extract_pattern(pattern: str, text: str, **kwargs) -> Optional[str]:
    """Yet another wrapper around extract_match for text input"""
    return extract_match(pattern, text.split("\n"), **kwargs)

def count_it(
        pattern: str,
        text: str,
        field: int = 1,
        multiple: Optional[None] = None
    ) -> Dict[str, int]:
    """Counts how often PATTERN's FIELD occurs in TEXT, returning hash.
    Note: By default MULTIPLE matches are tabulated"""
    # EX: dict(count_it("[a-z]", "Panama")) => {"a": 3, "n": 1, "m": 1}
    # EX: count_it("\w+", "My d@wg's fleas have fleas")["fleas"] => 2
    debug.trace(7, f"count_it({pattern}, _, {field}, {multiple}")
    value_counts: Dict[str, int] = defaultdict(int)
    for value in extract_matches_from_text(pattern, text, field, multiple):
        value_counts[value] += 1
    debug.trace_values(6, value_counts, "count_it()")
    return value_counts


def read_lines(
        filename: Optional[FileDescriptorOrPath] = None,
        make_unicode: bool = False
    ) -> List[str]:
    """Returns list of lines from FILENAME without newlines (or other extra whitespace)
    Note:
    - Uses stdin if filename is None. Optionally returned as unicode.
    - make_unicode is deprecated
    - Warning: deprecated function--use system.read_lines instead
    """
    debug.trace(3, "Warning: in deprecated glue_helpers.read_lines: use version in system")
    debug.assertion(not make_unicode)
    if not filename:
        filename = get_temp_file() + ".stdin.list"
        system.write_file(filename, system.read_all_stdin())
    return system.read_lines(filename)


def write_lines(
        filename: FileDescriptorOrPath,
        text_lines: List[str],
        append: bool = False
    ) -> None:
    """Creates FILENAME using TEXT_LINES with newlines added and optionally for APPEND
    Warning: deprecated function--use version in system.py instead"""
    debug.trace(3, "Warning: in deprecated glue_helpers.read_file: use version in system")
    system.write_lines(filename, text_lines, append=append)


def read_file(filename: FileDescriptorOrPath, make_unicode: bool = False) -> str:
    """Returns text from FILENAME (single string), including newline(s).
    Note: optionally returned as unicde.
    Warning: deprecated function--use system.read_file instead
    """
    debug.trace(3, "Warning: in deprecated glue_helpers.read_file: use version in system")
    debug.assertion(not make_unicode)
    return system.read_file(filename)


def write_file(filename: FileDescriptorOrPath, text: str, append: bool=False) -> None:
    """Writes FILENAME using contents in TEXT, adding trailing newline and optionally for APPEND
    Warning: deprecated function--use system.write_file instead
    """
    debug.trace(3, "Warning: in deprecated glue_helpers.write_file: use version in system")
    system.write_file(filename, text, append=append)


def copy_file(source: str, target: str) -> None:
    """Copy SOURCE file to TARGET file (or directory)"""
    # Note: meta data is not copied (e.g., access control lists)); see
    #    https://docs.python.org/2/library/shutil.html
    # TODO: have option to skip if non-dir target exists
    debug.trace(5, f"copy_file({source}, {target}")
    debug.assertion(non_empty_file(source))
    shutil.copy(source, target)
    if system.is_regular_file(target):
        target_file = target
    else:
        base = basename(source)
        assert isinstance(base, str)
        target_file = form_path(target, base)
    ## TODO: debug.assertion(file_size(source) == file_size(target_file))
    debug.assertion(non_empty_file(target_file))
    return


def non_empty_directory(path):
    """Whether PATH exists and is not empty"""
    size = len(get_directory_listing(path)) if is_directory(path) else -1
    non_empty = size > 0
    debug.trace_fmt(5, f"non_empty_directory({path}) => {non_empty}; (#files={size})")
    return non_empty


def copy_directory(source, dest):
    """copy SOURCE dir to DEST dir
    Note: The DEST directory must not exist beforehand
    """
    ## TODO4: add option to overwrite files (e.g., via copytree's dirs_exist_ok)
    # Note: meta data is not copied (e.g., access control lists)); see
    #    https://docs.python.org/3/library/shutil.html
    debug.trace_fmt(5, f"copy_directory({source}, {dest})")

    ## OLD: debug.assertion(non_empty_directory(source))
    dest_path = shutil.copytree(src=source, dst=dest)
    debug.assertion(len(get_directory_listing(source)) == len(get_directory_listing(dest_path)))
    ## OLD: debug.assertion(non_empty_directory(dest_path))


def rename_file(source: StrOrBytesPath, target: str) -> None:
    """Rename SOURCE file as TARGET file"""
    # TODO: have option to skip if target exists
    debug.trace(5, f"rename_file({source}, {target})")
    debug.assertion(non_empty_file(source))
    debug.assertion(source != target)
    os.rename(source, target)
    debug.assertion(non_empty_file(target))
    return


def delete_file(filename: StrOrBytesPath) -> bool:
    """Deletes FILENAME"""
    debug.trace(5, f"delete_file({filename})")
    debug.assertion(os.path.exists(filename))
    ok = False
    try:
        os.remove(filename)
        ok = True
        debug.trace_fmtd(6, "remove{f} => {r}", f=filename, r=ok)
    except OSError:
        ## OLD: debug.trace(5, "Exception during deletion of {filename}: " + str(sys.exc_info()))
        debug.trace_exception(5, f"deletion of {filename}")
    return ok


def delete_existing_file(filename: StrOrBytesPath) -> bool:
    """Deletes FILENAME if it exists and is not a directory or other special file"""
    ok = False
    if file_exists(filename):
        ok = delete_file(filename)
    debug.trace_fmtd(5, "delete_existing_file({f}) => {r}", f=filename, r=ok)
    return ok

def delete_directory(path):
    """Deletes directory at PATH
    Warning: Unless DISABLE_RECURSIVE_DELETE, this removes entire directory tree
    """
    debug.trace_fmt(5, f"delete_directory({path})")
    ok = False
    try:
        if DISABLE_RECURSIVE_DELETE:
            files = get_directory_listing(path)
            debug.trace(4, f"FYI: Only deleting top-level files in {path} to avoid potentially dangerous recursive deletion")
            for file in files:
                delete_file(form_path(path, file))
            ok = None
        else:
            debug.trace(4, f"FYI: Using potentially dangerous rmtree over {path}")
            shutil.rmtree(path)
            ok = None
    except OSError:
        debug.trace_fmt(5, f"Exception during deletion of {path}: {system.get_exception()}")
    return ok

def file_size(filename: FileDescriptorOrPath) -> int:
    """Returns size of FILENAME in bytes (or -1 if not found)"""
    size = -1
    if os.path.exists(filename):
        size = os.path.getsize(filename)
    debug.trace_fmtd(5, "file_size({f}) => {s}", f=filename, s=size)
    return size


def get_matching_files(pattern: str, warn: bool = False) -> List[str]:
    """Get sorted list of files matching PATTERN via shell globbing
    Note: Optionally issues WARNing"""
    # NOTE: Multiple glob specs not allowed in PATTERN
    files = sorted(glob.glob(pattern))
    debug.trace_fmtd(5, "get_matching_files({p}) => {l}",
                     p=pattern, l=files)
    if ((not files) and warn):
        system.print_stderr(f"Warning: no matching files for {pattern}")
    return files


def get_files_matching_specs(patterns: List[str]) -> List[str]:
    """Get list of files matching PATTERNS via shell globbing"""
    files = []
    for spec in patterns:
        files += get_matching_files(spec)
    debug.trace_fmtd(6, "get_files_matching_specs({p}) => {l}",
                     p=patterns, l=files)
    return files


def get_directory_listing(
        dir_name: Union[int, str, bytes],
        make_unicode: bool = False
    ) -> Union[List[str], List[str], List[bytes]]:
    """Returns files in DIR_NAME
    Note: make_unicode is deprecated
    """
    # TODO: Union[List[str], List[bytes]] = []
    ## TODO3: drop make_unicode; implement via system.get_directory_filenames
    all_file_names: Union[List[str], List[str], List[bytes]] = []
    try:
        all_file_names = os.listdir(dir_name)
    except OSError:
        debug.trace_fmtd(4, "Exception during get_directory_listing: {exc}",
                         exc=str(sys.exc_info()))
    if make_unicode:
        debug.trace(4, "Warning: using obsolete get_directory_listing make_unicode option")
    debug.trace_fmtd(5, "get_directory_listing({dir}) => {files}",
                     dir=dir_name, files=all_file_names)
    return all_file_names

#-------------------------------------------------------------------------------
# Extensions to system.py included here due to inclusion of functions 
# defined here.
## TODO3: put in system.py

def getenv_filename(var: str, default: str = "", description: Optional[str] = None) -> str:
    """Returns text filename based on environment variable VAR (or string version of DEFAULT) 
    with optional DESCRIPTION. This includes a sanity check for file being non-empty."""
    # EX: system.setenv("ETC", "/etc"); getenv_filename("ETC") => "/etc"
    # TODO4: explain motivation
    debug.trace_fmtd(6, "getenv_filename({v}, {d}, {desc})",
                 v=var, d=default, desc=description)
    if not description:
        description = ""
    filename = system.getenv_text(var, default, description)
    if filename and not non_empty_file(filename):
        system.print_stderr("Error: filename %s empty or missing for environment option %s" % (filename, var))
    return filename


if __debug__:

    assertion_deprecation_shown = False
    
    def assertion(condition: bool) -> None:
        """Issues warning if CONDITION doesn't hold
        Note: deprecated function--use debug.assertion instead"""
        global assertion_deprecation_shown
        if not assertion_deprecation_shown:
            debug.trace(3, "Warning: glue_helpers.assertion() is deprecated; use version in debug.py")
            assertion_deprecation_shown = True
        if debug.assertion(condition, indirect=True):
            try:
                frame = inspect.currentframe()
                frame = frame.f_back
                filename = frame.f_globals.get("__file__")
                line_num = frame.f_lineno
                debug.trace(TL.WARNING, f"FYI: Assertion failed at {filename}:{line_num}")
            except:
                system.print_exception_info("gh.assertion")
        return

else:

    def assertion(_condition: bool) -> None:
        """Non-debug stub for assertion"""
        return

def init() -> None:
    """Work around for Python quirk
    Note: This is also used for reinitialize temp-file settings such as for unit tests (e.g., TEMP_FILE from TEMP_BASE).
    Warning: The environment is used to reset following globals:
        PRESERVE_TEMP_FILE, TEMP_FILE, TEMP_LOG_FILE, TEMP_SCRIPT_FILE
    """
    global initialized
    # See https://stackoverflow.com/questions/1590608/how-do-i-forward-declare-a-function-to-avoid-nameerrors-for-functions-defined
    debug.trace(5, "glue_helpers.init()")
    ## OLD: temp_filename = f"{PID_BASENAME}.list"
    temp_filename = f"{PID_BASENAME}"
    if USE_TEMP_BASE_DIR and TEMP_BASE:
        ## OLD: full_mkdir(TEMP_BASE)
        pass

    # Re-initialize flag blocking TEMP_FILE init from TEMP_BASE
    global PRESERVE_TEMP_FILE
    PRESERVE_TEMP_FILE = system.getenv_bool(
        "PRESERVE_TEMP_FILE", None, allow_none=True, skip_register=initialized,
        desc="Retain value of TEMP_FILE even if TEMP_BASE set--see run and init below as well as unittest_wrapper.py")

    # note: Normally TEMP_FILE gets overriden when TEMP_BASE set. However,
    # this complicates preserving test-specific test files (see unittest_wrapper.py).
    # Further compications are due to the implicit module loading due to __init__.py.
    # See tests/test_unittest_wrapper.py for some diagnosis tips.
    temp_file_default = None
    if TEMP_BASE and not PRESERVE_TEMP_FILE:
        temp_file_default = (form_path(TEMP_BASE, temp_filename) if USE_TEMP_BASE_DIR else f"{TEMP_BASE}-{temp_filename}")
        debug.trace(4, f"FYI: Inferred TEMP_FILE default: {temp_file_default!r}")
    debug.trace_expr(5, system.getenv("TEMP_FILE"))
    global TEMP_FILE
    TEMP_FILE = system.getenv_value(
        "TEMP_FILE", temp_file_default, skip_register=initialized,
        description="Debugging override for temporary filename: avoid if possible")
    debug.trace_expr(5, system.getenv("TEMP_FILE"))
    #
    global TEMP_LOG_FILE
    TEMP_LOG_FILE = system.getenv_text(
        "TEMP_LOG_FILE", get_temp_file() + "-log", skip_register=initialized,
        description="Log file for stderr such as for issue function")
    global TEMP_SCRIPT_FILE
    TEMP_SCRIPT_FILE = system.getenv_text(
        "TEMP_SCRIPT_FILE", get_temp_file() + "-script", skip_register=initialized,
        description="File for command invocation")
    initialized = True
#
init()

def main() -> None:
    """Entry point"""
    # Uses dynamic import to avoid circularity
    from mezcla.main import Main        # pylint: disable=import-outside-toplevel
    
    # Note: Uses main-based arg parsing for sake of show environment options
    #   ./glue_helpers.py --help --verbose
    debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")

    # Parse command line options, show usage if --help given
    main_app = Main(description=__doc__.format(script=basename(__file__)))
    debug.assertion(main_app.parsed_args)
    return
    
#------------------------------------------------------------------------

# Warn if invoked standalone
#
if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    system.print_stderr(f"Warning: {__file__} is not intended to be run standalone\n")
    main()
