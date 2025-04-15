#! /usr/bin/env python3
#
# extract_document_text.py: extract text from documents of various types
#
# NOTE:
# - Mostly a wrapper around functionality in textract package.
# - By default a suffix is added to the entire filename (e.g., fubar.docx.txt.1apr18),
#   but an affix can be used instead (e.g., fubar.docx.1apr18.txt).
#
# TODO:
# - Use file date for default date affix.
# - Handle UTF8.
#
#

"""Extract text from common document types"""

# Standard packages
import sys
import datetime

# Installed packages
import textract

# Local packages
from mezcla import system
from mezcla import debug
from mezcla import glue_helpers as gh


# Determine environment-based options
STDOUT = system.getenv_boolean("STDOUT", False)
## TODO: USE_TODAY = system.getenv_boolean("USE_TODAY", False)
## TODO: use new misc_util.get_date_ddmmmyy()
TODAY_DDMMMYY = datetime.date.today().strftime("%d%b%y").lower()
ADD_DATE = system.getenv_boolean("ADD_DATE", False)
DEFAULT_SUFFIX = "" if (STDOUT or not ADD_DATE) else TODAY_DDMMMYY
HTML = system.getenv_bool("HTML", False, desc="Assume HTML input")
DOC = system.getenv_bool("DOC", False, desc="Assume MS document input")
DEFAULT_IN_TYPE = ("html" if HTML else "doc" if DOC else "txt")
IN_TYPE = system.getenv_text("IN_TYPE", DEFAULT_IN_TYPE,
                             desc="Input file type--ext w/o period")
OUT_TYPE = system.getenv_text("OUT_TYPE", "txt",
                              desc="Input file type--ext w/o period")
EXT = system.getenv_text("EXT", f".{IN_TYPE}")
IN_EXT = EXT
SUFFIX = system.getenv_text("SUFFIX", DEFAULT_SUFFIX)
USE_AFFIX = system.getenv_boolean("USE_AFFIX", False)
FORCE = system.getenv_boolean("FORCE", False)
EXTENSION = system.getenv_value("EXTENSION", f".{OUT_TYPE}",
                                "Extension of file for conversion")
OUT_EXT = EXTENSION

def show_usage_and_quit():
    """Show command-line usage for script and then exit"""
    ## OLD:
    ## usage = """
## Usage: {prog} [options] [input-dir] [output-file]

    usage = """
Usage: {prog} [options] [input-file] ...

Options: [--help]

Notes:
- Converts documents to text
- Use following environment options:
  STDOUT: Send all output to standard output.
  IN_EXT: File type for unnamed input (e.g., .html)
  OUT_EXT: File extension for output text file (e.g., .txt)
  SUFFIX: New suffix for output text file (e.g., [.txt].copy).
  ADD_DATE: Add date as suffix or affix (e.g., .txt.17mar18).
  USE_AFFIX: Put suffix before file extension (e.g., .copy[.txt]).
"""
    print(usage.format(prog=sys.argv[0]))
    sys.exit()


def document_to_text(doc_filename):
    """Returns text version of document FILENAME of unspecified type"""
    debug.trace(4, f"document_to_text({doc_filename})")
    debug.trace_expr(4, IN_EXT)
    text = ""
    OK = False
    try:
        text = textract.process(doc_filename).decode("UTF-8")
        OK = True
    except ImportError:
        debug.trace_fmtd(3, "FYI: import error converting file {f}: {e}",
                         f=doc_filename, e=sys.exc_info())

    if not OK:
        try:
            ## OLD: text = system.from_utf8(textract.process(doc_filename))
            text = textract.process(doc_filename,
                                    extension=IN_EXT
                                    ).decode("UTF-8")
        except:
            debug.trace_fmtd(3, "Warning: problem converting document file {f}: {e}",
                             f=doc_filename, e=sys.exc_info())
    debug.trace(4, f"document_to_text() => {gh.elide(text)!r}")
    return text


def main():
    """Entry point for script"""
    args = sys.argv[1:]
    debug.trace_fmtd(5, "main(): args={a}", a=args)
    affix = ""
    suffix = ""
    if SUFFIX:
        if USE_AFFIX:
            affix = ("." + SUFFIX)
        else:
            suffix = ("." + SUFFIX)
    debug.trace_fmtd(4, "affix={a} suffix={s}", a=affix, s=suffix)
    use_stdout = STDOUT

    # Parse command-line arguments
    i = 0
    if (not args):
        show_usage_and_quit()
    while (args[i].startswith("--")):
        option = args[i]
        if (option == "--help"):
            show_usage_and_quit()
        else:
            sys.stderr.write("Error: unknown option '{o}'\n".format(o=option))
            show_usage_and_quit()
        i += 1

    # Process each of the arguments
    for filename in args:
        # Use stdio if no filename specified (i.e., -)
        if (filename == "-"):
            filename = gh.get_temp_file() + IN_EXT
            system.write_file(filename, system.read_all_stdin())
            use_stdout = True

        # Warning that HTML not well supported
        if (not HTML and filename.endswith(".html")):
            system.print_error("Warning: HTML not well supported; use html_utils.html_to_text instead")
            
        # Read in file contents
        text = document_to_text(filename)

        # Write output, using text extension unless stdout
        ## TODO: file_date = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
        if use_stdout:
            sys.stdout.write(system.to_utf8(text) + "\n")
        else:
            new_filename = system.remove_extension(filename) + affix + OUT_EXT + suffix
            if system.non_empty_file(new_filename) and not FORCE:
                system.print_stderr("Error: file {nf} exists. Use FORCE to overwrite".
                                    format(nf=new_filename))
            else:
                system.write_file(new_filename, text)
                print(new_filename)

    return

#------------------------------------------------------------------------

if __name__ == '__main__':
    main()
