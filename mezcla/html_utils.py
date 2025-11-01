#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Micellaneous HTML utility functions, in particular with support for resolving HTML
# rendered via JavaScript (using selenium). This was motivated by the desire to extract
# images from pubchem.ncbi.nlm.nih.gov web pages for drugs (e.g., Ibuprofen, as
# illustrated below).
#
#-------------------------------------------------------------------------------
# Example usage:
#
# TODO3: see what html_file should be set to
# $ PATH="$PATH:/usr/local/programs/selenium" DEBUG_LEVEL=6 HEADLESS_WEBDRIVER=1 $PYTHON html_utils.py "$html_file" > _html-utils-pubchem-ibuprofen.log 2>&1
# $ cd $TMPDIR
# $ wc *ibuprofen*
#     13   65337  954268 post-https%3A%2F%2Fpubchem.ncbi.nlm.nih.gov%2Fcompound%2FIbuprofen
#   3973   24689  178909 post-https%3A%2F%2Fpubchem.ncbi.nlm.nih.gov%2Fcompound%2FIbuprofen.txt
#     60    1152   48221 pre-https%3A%2F%2Fpubchem.ncbi.nlm.nih.gov%2Fcompound%2FIbuprofen
#
# $ count_it.perl "<img" pre-https%3A%2F%2Fpubchem.ncbi.nlm.nih.gov%2Fcompound%2FIbuprofen
# $ count_it.perl "<img" post-https%3A%2F%2Fpubchem.ncbi.nlm.nih.gov%2Fcompound%2FIbuprofen
# <img  7
#
# $ diff pre-https%3A%2F%2Fpubchem.ncbi.nlm.nih.gov%2Fcompound%2FIbuprofen post-https%3A%2F%2Fpubchem.ncbi.nlm.nih.gov%2Fcompound%2FIbuprofen
# ...
# <   <body>
# <     <div id="js-rendered-content"></div>
# ---
# > 
# >     <div id="js-rendered-content"><div class="relative flex-container-vertical"><header class="bckg-white b-bottom"><div class="bckg
# 54c7
# <     <script type="text/javascript" async src="/pcfe/summary/summary-v3.min.js"></script><!--<![endif]-->
# ---
# >     <script type="text/javascript" async="" src="/pcfe/summary/summary-v3.min.js"></script><!--<![endif]-->
# 58,60c11,13
# <     <script type="text/javascript" async src="https://www.ncbi.nlm.nih.gov/core/pinger/pinger.js"></script>
# <   </body>
#
#................................................................................
# Note:
# - via https://dirask.com/posts/JavaScript-difference-between-innerHTML-and-outerHTML-MDg8mp:
#   The difference between innerHTML and outerHTML html:
#     innerHTML = HTML inside of the selected element
#     outerHTML = HTML inside of the selected element + HTML of the selected element
# - via grok:
#   In short, inner HTML is just the content inside the tags, while outer HTML includes the tags themselves.
#-------------------------------------------------------------------------------
# TODO3:
# - Standardize naming convention for URL parameter accessors (e.g., get_url_param vs. get_url_parameter).
# - Create class for selenium support (e.g., get_browser ... wait_until_ready).
# - * Use kawrgs to handle functions with common arguments (e.g., download_web_document, retrieve_web_document, and wrappers around them).
# - Use thin spacing around controls (e.g., via U+202F Narrow No-Break Space or via CSS).
#
# TODO2:
# - Document selenium/webdriver installation (e.g., gecko drivers).
# 

"""HTML utility functions"""

# Standard packages
import html
import sys
import time
import traceback
import urllib.request
from urllib.error import HTTPError, URLError
from http.client import HTTPMessage
try:
    # pylint: disable=no-name-in-module
    from typing_extensions import Any, Callable, Dict, List, Optional, Union
except:
    ## TODO: debug.raise()
    ## TEMP:
    traceback.print_exc(file=sys.stderr)
    sys.stderr.write(f"Error importing extensions: {sys.exc_info()}\n")
    sys.exit("Error: html_utils.py requires Python typing_extensions >= 4.7.0 (backport limitations with typing_extensions)")

# Installed packages
# Note: selenium import now optional; BeautifulSoup also optional
import requests

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import misc_utils
from mezcla import system
write_temp_file = gh.write_temp_file

# Constants
TL = debug.TL
DEFAULT_STATUS_CODE = 0
MAX_DOWNLOAD_TIME = system.getenv_float(
    "MAX_DOWNLOAD_TIME", 30,
    description="Time in seconds for rendered-HTML download as with get_inner_html")
MID_DOWNLOAD_SLEEP_SECONDS = system.getenv_float(
    "MID_DOWNLOAD_SLEEP_SECONDS", 1,
    description="Mid-stream delay if document not ready")
NUM_MID_DOWNLOAD_CHECKS = system.getenv_integer(
    "NUM_MID_DOWNLOAD_CHECKS", 3,
    description="Number of mid-stream delays to use")
POST_DOWNLOAD_SLEEP_SECONDS = system.getenv_float(
    "POST_DOWNLOAD_SLEEP_SECONDS", 1,
    description="Courtesy delay after URL access--prior to download")
SKIP_BROWSER_CACHE = system.getenv_boolean(
    "SKIP_BROWSER_CACHE", False,
    description="Don't use cached webdriver browsers")
USE_BROWSER_CACHE = not SKIP_BROWSER_CACHE
DOWNLOAD_DIR = system.getenv_text(
    "DOWNLOAD_DIR", "downloads",
    description="Default download directory")
DOWNLOAD_VIA_URLLIB = system.getenv_bool(
    "DOWNLOAD_VIA_URLLIB", False,
    description="Use old-style download via urllib instead of requests")
DOWNLOAD_VIA_REQUESTS = (not DOWNLOAD_VIA_URLLIB)
DOWNLOAD_TIMEOUT = system.getenv_float(
    "DOWNLOAD_TIMEOUT", 5,
    description="Timeout in seconds for request-based as with download_web_document")
HEADLESS_WEBDRIVER = system.getenv_bool(
    "HEADLESS_WEBDRIVER", True,
    description="Whether Selenium webdriver is hidden")
KIOSK_MODE = system.getenv_bool(
    "KIOSK_MODE", False,
    description="Run browser in kiosk mode (e.g., no window controls)")
OMIT_STABLE_DOWNLOAD_CHECK = system.getenv_bool(
    "OMIT_STABLE_DOWNLOAD_CHECK", False,
    description="Omit waiting until download size stablizes--for dynamic content")
STABLE_DOWNLOAD_CHECK = not OMIT_STABLE_DOWNLOAD_CHECK
EXCLUDE_IMPORTS = system.getenv_bool(
    "EXCLUDE_IMPORTS", False,
    description="Sets --follow-imports=silent; no import files are checked")
TARGET_BOOTSTRAP =  system.getenv_bool(
    "TARGET_BOOTSTRAP", False,
    description="Format tooltips, etc. for use with bootstrap")
CHROME_WEBDRIVER = system.getenv_bool(
    "CHROME_WEBDRIVER", False,
    description="Use Chrome webdriver for Selenium")
FIREFOX_WEBDRIVER = system.getenv_bool(
    "FIREFOX_WEBDRIVER", not CHROME_WEBDRIVER,
    description="Use Firefox webdriver for Selenium")
FIREFOX_PATH = system.getenv_value(     ## TODO3: rename as FIREFOX_DRIVER_PATH
    "FIREFOX_PATH", None,
    desc="Path override for Firefox webdriver (e.g., geckodriver)")
CHROME_PATH = system.getenv_value(      ## TODO3: rename as CHROME_DRIVER_PATH
    "CHROME_PATH", None,
    desc="Path override for Chrome webdriver")
WEBDRIVER_PATH = system.getenv_value(
    "WEBDRIVER_PATH", (FIREFOX_PATH if FIREFOX_WEBDRIVER else CHROME_PATH),
    desc="Path override for webdriver binary for use with selenium")
BROWSER_DIMENSIONS = system.getenv_value(
    "BROWSER_DIMENSIONS", None,
    desc="WxH Dimensions for browser with Selenium/URL--allows higher resolution with headless")
BROWSER_PATH = system.getenv_value(
    "BROWSER_PATH", None,
    desc="Path override for browser binary (for use with selenium)")
BROWSER_TIMEOUT = system.getenv_value(
    "TIMEOUT", None,
    description="Time in seconds for selenium broswer load")

HEADERS = "headers"
FILENAME = "filename"
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'

# Custom Types
OptStrBytes = Union[str, bytes, None]
OptBoolStr = Union[bool, str, None]

# Globals
# note: for convenience in Mako template code
user_parameters : Dict[str, str] = {}
issued_param_dict_warning : bool = False

# Placeholders for dynamically loaded modules
BeautifulSoup : Optional[Callable] = None

# Conditional imports
try:
    from selenium import webdriver
    from selenium.webdriver.remote.webdriver import WebDriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.firefox.service import Service as FirefoxService
except:
    debug.trace_exception(5, "selenium imports")
    webdriver = None
    WebDriver = object
    ChromeService = None
    FirefoxService = None

#-------------------------------------------------------------------------------
# HTML utility functions

browser_cache : Dict = {}
##
def get_browser(url : str, timeout : Optional[float] = None) -> Optional[WebDriver]:
    """Get existing browser for URL or create new one
    Notes: 
    - This is for use in web automation (e.g., via selenium).
    - A large log file might be produced (e.g., geckodriver.log).
    - If TIMEOUT specified, it only waits specified seconds.
    - Warning: can return null browser object.
    """
    ## TODO3: create a class-based interface to simplify repeated us
    if timeout is None:
        timeout = BROWSER_TIMEOUT
    debug.trace(4, f"in get_browser({url}); {timeout=}")
    browser : Optional[WebDriver] = None
    global browser_cache

    # Check for cached version of browser. If none, create one and access page.
    browser = browser_cache.get(url) if USE_BROWSER_CACHE else None
    if not browser:
        try:
            # Make the browser hidden by default (i.e., headless)
            # See https://stackoverflow.com/questions/46753393/how-to-make-firefox-headless-programmatically-in-selenium-with-python.
            options_module = (webdriver.firefox.options if FIREFOX_WEBDRIVER else webdriver.chrome.options)
            webdriver_options = options_module.Options()

            if BROWSER_PATH:
                webdriver_options.binary_location = BROWSER_PATH
                debug.assertion(system.file_exists(BROWSER_PATH))
                debug.trace(4, f"Warning: overriding webdriver path: {webdriver_options.binary_location=}")
            if HEADLESS_WEBDRIVER:
                webdriver_options.add_argument('-headless')
            if KIOSK_MODE:
                webdriver_options.add_argument('-kiosk')
            debug.trace_object(5, webdriver_options)
            debug.assertion(not (FIREFOX_WEBDRIVER and CHROME_WEBDRIVER))
            if FIREFOX_WEBDRIVER:
                service = FirefoxService(executable_path=WEBDRIVER_PATH) if WEBDRIVER_PATH else None
                browser = webdriver.Firefox(service=service, options=webdriver_options)
            else:                        # CHROME_WEBDRIVER
                service = ChromeService(executable_path=WEBDRIVER_PATH) if WEBDRIVER_PATH else None
                browser = webdriver.Chrome(service=service, options=webdriver_options)
            if BROWSER_DIMENSIONS:
                dims = [system.to_float(d) for d in misc_utils.extract_string_list(BROWSER_DIMENSIONS)]
                debug.assertion(len(dims) == 2)
                browser.set_window_size(*dims)
            if debug.get_level() >= 6:
                debug.trace_fmt(1, "Window dimensions: {w}x{h}",
                                w=browser.execute_script("return window.outerWidth"),
                                h=browser.execute_script("return window.outerHeight"))
            if timeout:
                ## TODO2: determine way for timeout to honored without timeout exception during get below
                debug.assertion(False, "Selenium timeout support not functional")
                browser.set_page_load_timeout(system.to_float(timeout))
            debug.trace_object(5, browser)
    
            # Load the page, setting optional cache entry
            if USE_BROWSER_CACHE:
                browser_cache[url] = browser
            browser.get(url)
    
            # Optionally pause after accessing the URL (to avoid overloading the same server).
            # Note: This assumes that the URL's are accessed sequentially. ("Post-download" is
            # a bit of a misnomer as this occurs before the download from browser, as in get_inner_html.)
            if POST_DOWNLOAD_SLEEP_SECONDS:
                system.sleep(POST_DOWNLOAD_SLEEP_SECONDS, message="Post-download")
        except:
            browser = None
            debug.raise_exception(6)
            system.print_exception_info("get_browser")

    # Make sure the bare minimum is included (i.e., "<body></body>" of length 13)
    if browser:
        debug.assertion(len(browser.execute_script("return document.body.outerHTML") or "") >= 13)
    debug.trace_fmt(5, "get_browser({u}) => {b}", u=url, b=browser)
    return browser


def shutdown_browser(browser: WebDriver) -> None:
    """Close the browser web driver instance"""
    try:
        browser.close()
        browser.quit()
    except:
        system.print_exception_info("shutdown_browser")
    return


def get_inner_html(url : str, browser: Optional[WebDriver] = None) -> str:
    """Return the fully-rendered version of the URL HTML source (e.g., after JavaScript DOM manipulation)
    Note:
    - requires selenium webdriver (browser specific)
    - previously implemented via document.body.innerHTML (hence name)"""
    # Based on https://stanford.edu/~mgorkove/cgi-bin/rpython_tutorials/Scraping_a_Webpage_Rendered_by_Javascript_Using_Python.php
    # Also see https://stackoverflow.com/questions/8049520/web-scraping-javascript-page-with-python.
    # Note: The retrieved HTML might not match the version rendered in a browser due to a variety of reasons such as timing of dynamic updates and server controls to minimize web crawling.
    debug.trace_fmt(5, "get_inner_html({u})", u=url)
    inner_html: str = ""
    try:
        if browser is None:
            # Navigate to the page (or get browser instance with existing page)
            browser = get_browser(url)
        if browser:
            # Wait for Javascript to finish processing
            wait_until_ready(url)
            # Extract fully-rendered HTML
            inner_html = browser.page_source
    except:
        system.print_exception_info("get_inner_html")
    debug.trace_fmt(7, "get_inner_html({u}) => {h}", u=url, h=inner_html)
    return inner_html


def get_inner_text(url : str, browser: Optional[WebDriver] = None) -> str:
    """Get text of URL (i.e., without HTML tags) after JavaScript processing (via selenium)"""
    debug.trace_fmt(5, "get_inner_text({u})", u=url)
    # See https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/innerText
    inner_text: str = ""
    try:
        if browser is None:
            # Navigate to the page (or get browser instance with existing page)
            browser = get_browser(url)
        if browser:
            # Wait for Javascript to finish processing
            wait_until_ready(url, browser=browser)
            # Extract fully-rendered text
            inner_text = browser.execute_script("return document.body.innerText")
    except:
        debug.trace_exception(6, "get_inner_text")
        system.print_exception_info("get_inner_text")
    debug.trace_fmt(7, "get_inner_text({u}) => {it}", u=url, it=inner_text)
    return inner_text


def browser_command(url: str, command: str, timeout : Optional[float] = None,
                    browser: Optional[WebDriver] = None) -> Any:
    """Issue COMMAND to BROWSER via selenium (for URL) with optional TIMEOUT.
    The command is part of the browser API (not the python API): for latter, see selenium_function.
    """
    # example: return document.contentType
    result: Any = None
    try:
        if browser is None:
            browser = get_browser(url, timeout=timeout)
        if browser:
            result = browser.execute_script(command)
    except:
        system.print_exception_info(f"browser_command {command!r}")
    debug.trace_fmt(5, "browser_command({u}, {c}, [{to}, {b}]) => {r}",
                    u=url, c=command, r=result, b=browser, to=timeout)
    return result


def document_ready(url : str, timeout : Optional[float] = None,
                   browser: Optional[WebDriver] = None) -> bool:
    """Determine whether document for URL has completed loading (via selenium).
    Note: If TIMEOUT specified, it only waits specified seconds.
    """
    # See https://developer.mozilla.org/en-US/docs/Web/API/Document/readyState
    ready_state: str = browser_command(url, "return document.readyState", timeout=timeout, browser=browser)
    is_ready: bool = (ready_state == "complete")
    debug.trace_fmt(6, "document_ready({u}, [{to}, {b}]) => {r}; state={s}",
                    u=url, to=timeout, r=is_ready, s=ready_state, b=browser)
    return is_ready


def wait_until_ready(url : str, stable_download_check : Optional[bool] = None,
                     browser: Optional[WebDriver] = None) -> None:
    """Wait for document_ready (q.v.) and pause to allow loading to finish (via selenium)
    Note: If STABLE_DOWNLOAD_CHECK, the wait incoporates check for download size differences"""
    # TODO: make sure the sleep is proper way to pause
    debug.trace_expr(5, url, stable_download_check, browser,
                     prefix="in wait_until_ready: ")
    if stable_download_check is None:
        stable_download_check = STABLE_DOWNLOAD_CHECK
    debug.trace_expr(6, stable_download_check)
    start_time = time.time()
    end_time = start_time + MAX_DOWNLOAD_TIME
    if browser is None:
        browser = get_browser(url)
    last_size = -1
    size = 0
    done = False

    # Wait until document ready and optionally that the size is the same after a delay
    # and for a specified number of checks (e.g., same size for 3 checks).
    count = 0
    while (browser and (time.time() < end_time) and (not done)):
        done = document_ready(url, browser=browser)
        if (done and stable_download_check):
            size = len(browser.page_source)
            done = (size == last_size)
            if done:
                count += 1
                done = (count == NUM_MID_DOWNLOAD_CHECKS)
            else:
                count = 0
            diff = (size - last_size) if (last_size > -1) else size
            debug.trace_fmt(5, "Stable size check: last={l} size={s} diff={df} count={c} done={d}",
                            l=last_size, s=size, c=count, d=done, df=diff)
            last_size = size
        if not done:
            system.sleep(MID_DOWNLOAD_SLEEP_SECONDS, message="Mid-stream download")

    # Issue warning if unexpected condition
    if (not document_ready(url, browser=browser)):
        debug.trace_fmt(5, "Warning: time out ({s} secs) in accessing URL '{u}')'",
                        s=system.round_num(end_time - start_time, 1), u=url)
    elif (stable_download_check and (size > last_size)):
        debug.trace_fmt(5, "Warning: size not stable after {s} secs when accessing URL '{u}')'",
                        s=system.round_num(end_time - start_time, 1), u=url)
    debug.trace_fmt(5, "out wait_until_ready; elapsed={t}s",
                    t=(time.time() - start_time))
    return


def selenium_function(url: str, function: Optional[str] = None, args: Optional[str] = None,
                      call: Optional[str] = None, timeout : Optional[float] = None,
                      browser: Optional[WebDriver] = None) -> Any:
    """Evaluate selenium FUNCTION with ARGS using BROWSER (for URL).
    The function is part of the python API (not the browser API): for latter, see browser_command.
    With optional CALL specified, the function and args are ignored.
    Note: This is just a wrapper around FUNCTION(ARGS) with tracing and exception handling.
    """
    # example: get_screenshot_as_file("output-files/modern-art-4x3.png")
    if args is None:
        args = ""
    if call is None:
        call = f"{function}({args})"
    else:
        debug.assertion(not function, "Use CALL or FUNCTION but not both")
    result: Any = None
    try:
        if browser is None:
            browser = get_browser(url, timeout=timeout)
        if browser:
            # pylint: disable=eval-used
            result = eval(f"browser.{call}")
    except:
        system.print_exception_info(f"selenium_function {function!r})")
    debug.trace_fmt(5, "selenium_function({u}, {f}, {a}, [{b}]) => {r}",
                    u=url, f=function, a=args, r=result, b=browser)
    return result


def save_browser_screenshot(url, path: str, browser: Optional[WebDriver] = None) -> bool:
    """Save screenshot for URL to PATH using BROWSER"""
    return selenium_function(url, "get_screenshot_as_file", args=path, browser=browser)


def get_browser_log(url, browser: Optional[WebDriver] = None) -> bool:
    """Get console log for URL using BROWSER"""
    return selenium_function(url, "get_log", args="'browser'", browser=browser)

#...............................................................................

def escape_hash_value(hash_table : Dict, key: str):
    """Wrapper around escape_html_value for HASH_TABLE[KEY] (or "" if missing).
    Note: newlines are converted into <br>'s."""
    escaped_item_value = escape_html_value(hash_table.get(key, ""))
    escaped_value = escaped_item_value.replace("\n", "<br>")
    debug.trace_fmtd(7, "escape_hash_value({h}, {k}) => '{r}'", h=hash_table, k=key, r=escaped_value)
    return escaped_value


def get_param_dict(param_dict : Optional[Dict] = None) -> Dict:
    """Returns parameter dict using PARAM_DICT if non-Null else global USER_PARAMETERS
       Note: The PARAM_DICT argument can be used by functions like get_url_parameter_value 
       to allow thread-safe access for different users (see set_param_dict)."""
    result = (param_dict if (param_dict is not None) else user_parameters)
    debug.trace(7, f"get_param_dict([pd={param_dict}]) => {result}")
    return result


def set_param_dict(param_dict : Dict) -> None:
    """Sets global user_parameters to value of PARAM_DICT.
    Warning: not thread-safe (see get_param_dict).
    """
    # EX: set_param_dict({"param1": "a+b+c", "param2": "a%2Bb%2Bc"}); len(user_parameters) => 2
    debug.trace(7, f"set_param_dict({param_dict})")
    global issued_param_dict_warning
    global user_parameters

    # Make update, issuing warning if first time
    if not issued_param_dict_warning:
        issued_param_dict_warning = True
        debug.trace(5, "Warning: set_param_dict is not thread-safe")
    user_parameters = param_dict


def get_url_param(name : str, default_value : Optional[str] = None, param_dict : Optional[Dict] = None, escaped : bool = False):
    """Get value for NAME from PARAM_DICT (e.g., USER_PARAMETERS), using DEFAULT_VALUE (normally "").
    Note: It can be ESCAPED for use in HTML. Underscores in NAME are converted to dashes if not in dict.
    Warning: Can return a list (unlike get_url_parameter_value).
    """
    # EX: get_url_param("fu", param_dict={"fu": "123"}) => "123"
    # EX: get_url_param("fu", param_dict={"fu": ["123", "321"]}) => ["123", "321"]
    # TODO3: default_value => default; rename as get_url_param_raw
    if default_value is None:
        default_value = ""
    param_dict = (get_param_dict(param_dict) or {})
    if "_" in name and (name not in param_dict):
        name = name.replace("_", "-")
    value = param_dict.get(name, default_value)
    value = system.to_unicode(value)
    if escaped:
        value = escape_html_value(value)
    debug.trace_fmt(5, "get_url_param({n}, [{d}]) => {v})",
                    n=name, d=default_value, v=value)
    return value
#
get_url_parameter = get_url_param


def get_url_text(name : str, default_value : Any = None, param_dict : Optional[Dict] = None):
    """Get TEXT value for URL encoded parameter, using current PARAM_DICT"""
    # EX: get_url_text("param1") => "a b c"
    encoded_vaue = get_url_parameter(name, default_value, param_dict)
    value = unescape_html_value(system.unquote_url_text(encoded_vaue))
    debug.trace_fmt(6, "get_url_text({n}, [d={d}]) => {v})",
                    n=name, d=param_dict, v=value)
    return value
#
# EX: get_url_text("param2") => "a+b+c"           # where '+' is 0x2B
   

def get_url_param_checkbox_spec(name : str, default_value : OptBoolStr = "", param_dict : Optional[Dict] = None):
    """Get value of boolean parameters formatted for checkbox (i.e., 'checked' iff True or on) from PARAM_DICT
    Note: the value is only specified/submitted if checked"""
    # EX: get_url_param_checkbox_spec("param", param_dict={"param": "on"}) => "checked"
    # EX: get_url_param_checkbox_spec("param", param_dict={"param": "off"}) => ""
    # NOTE: 1 also treated as True
    # TODO: implement in terms of get_url_param
    param_dict = (get_param_dict(param_dict) or {})
    param_value = param_dict.get(name, default_value)
    if isinstance(param_value, list):
        param_value = param_value[-1]
    param_value = system.to_unicode(param_value)
    value = "checked" if system.to_bool(param_value) else ""
    debug.trace_fmtd(4, "get_url_param_checkbox_spec({n}, [{d}]) => {v})",
                     n=name, d=default_value, v=value)
    return value
#
get_url_parameter_checkbox_spec = get_url_param_checkbox_spec


def get_url_parameter_value(param, default_value : Any = None, param_dict : Optional[Dict] = None):
    """Get (last) value for PARAM in PARAM_DICT (or DEFAULT_VALUE)
    Note: Underscores in PARAM are converted to dashes if not in dict.
    Also, different from get_url_parameter in just returning single value.    
    Warning: empty strings are treated as None.
    """
    # EX: get_url_parameter_value("fu", param_dict={"fu": ["123", "321"]}) => "321"
    # TODO3?: rename as get_last_url_parameter_value (to avoid confusion with get_url_parameter)
    param_dict = (get_param_dict(param_dict) or {})
    in_param = param
    if "_" in param and (param not in param_dict):
        param = param.replace("_", "-")
    result = (param_dict.get(param) or default_value)
    if isinstance(result, list):
        result = result[-1]
    debug.trace_fmtd(5, "get_url_parameter_value({p}, {dft}, _) => {r!r}",
                     p=in_param, dft=default_value, r=result)
    return result
#
# EX: get_url_parameter_value("fu", param_dict={"fu": "321"}) => "321"

def get_url_parameter_bool(param, default_value : bool = False, param_dict : Optional[Dict] = None):
    """Get boolean value for PARAM from PARAM_DICT, with "on" treated as True. @note the hash defaults to user_parameters, and the default value is False
    Note: Only treates {"1", "on", "True", True} as True.
    Warning: defaults with non-None values might return unintuitive results unless
    coerced to boolean beforehand.
    """
    # EX: get_url_parameter_bool("abc", False, { "abc": "on" }) => True
    debug.assertion((default_value is None) or isinstance(default_value, bool))
    value = get_url_parameter_value(param, default_value, param_dict)
    result = system.to_bool(value)
    ## HACK: result = ((system.to_unicode(param_dict.get(param, default_value))) in ["on", True])
    debug.trace_fmtd(4, "get_url_parameter_bool({p}, {dft}, _) => {r}",
                     p=param, dft=default_value, r=result)
    return result
#
get_url_param_bool = get_url_parameter_bool
#
# EX: get_url_param_bool("abc", False, param_dict={"abc": "True"}) => True


def get_url_parameter_int(param, default_value : int = 0, param_dict : Optional[Dict] = None) -> int:
    """Get integer value for PARAM from PARAM_DICT.
    Note: the hash defaults to user_parameters, and the default value is 0"""
    result = system.to_int(get_url_parameter_value(param, default_value, param_dict))
    debug.trace_fmtd(4, "get_url_parameter_int({p}, {dft}, _) => {r}",
                     p=param, dft=default_value, r=result)
    return result
#
get_url_param_int = get_url_parameter_int
#
# EX: get_url_parameter_int("n", param_dict={"n": "1"}) => 1
# EX: get_url_parameter_int("_", param_dict={"_": "_"}) => 0


def get_url_parameter_float(param, default_value : float = 0.0, param_dict : Optional[Dict] = None) -> float:
    """Get floating-point value for PARAM from PARAM_DICT.
    Note: the hash defaults to user_parameters, and the default value is 0.0"""
    result = system.to_float(get_url_parameter_value(param, default_value, param_dict))
    debug.trace_fmtd(4, "get_url_parameter_float({p}, {dft}, _) => {r}",
                     p=param, dft=default_value, r=result)
    return result
#
get_url_param_float = get_url_parameter_float


def fix_url_parameters(url_parameters : Dict):
    """Uses the last values for any user parameter with multiple values
    and ensures dashes are used instead of embedded underscores in the keys"""
    # EX: fix_url_parameters({'w_v':[7, 8], 'h_v':10}) => {'w-v':8, 'h-v':10}
    # EX: fix_url_parameters({'_':'_'}) => {'_':'_'}
    new_url_parameters = {my_re.sub(r"([a-z0-9])_", r"\1-", p):v
                          for  (p, v) in url_parameters.items()}
    new_url_parameters = {p:(v[-1] if isinstance(v, list) else v) for (p, v) in new_url_parameters.items()}
    debug.trace_fmt(6, "fix_url_parameters({up}) => {new}",
                    up=url_parameters, new=new_url_parameters)
    return new_url_parameters


def expand_misc_param(misc_dict : Dict, param_name : str, param_dict : Optional[Dict] = None):
    """Expands MISC_DICT to include separate keys for those in PARAM_DICT under PARAM_NAME
    Notes:
    - The parameter specification is comma separated. 
    - PARAM_DICT defaults to the global user_parameters (or MISC_DICT if unset): see set_param_dict.
    - This was added to support having multiple user parameters specified in an HTML field.
    """
    # EX: expand_misc_param({'x': 1, 'y': 2, 'z': 'a=3, b=4'}, 'z') => {'x': 1, 'y':, 2, 'z': 'a=3 b=4', 'a': '3', 'b': '4'}
    debug.trace(6, f"expand_misc_param({misc_dict}, {param_name}, {param_dict})")
    ## TODO: debug.trace_expr(6, misc_dict, param_name, param_dict=None, prefix="expand_misc_param: ")
    ## TODO3: document more of the logic
    if param_dict is None:
        param_dict = (user_parameters or misc_dict)
    new_misc_dict = misc_dict
    misc_params = get_url_param(param_name, "", param_dict=param_dict)
    if (misc_params and ("=" in misc_params)):
        new_misc_dict = new_misc_dict.copy()
        for param_spec in my_re.split(", *", misc_params):
            if not param_spec.strip():
                continue
            try:
                param_key, param_value = param_spec.split("=")
                new_misc_dict[param_key] = param_value
            except:
                system.print_exception_info("expand_misc_param")
    debug.trace(5, f"expand_misc_param() => {new_misc_dict}")
    return new_misc_dict


def _read_file(filename : str, as_binary : bool) -> OptStrBytes:
    """Wrapper around read_entire_file or read_binary_file if AS_BINARY"""
    ## TODO2: allow for ignoring UTF-8 errors
    debug.trace(8, f"_read_file({filename}, {as_binary})")
    read_fn = system.read_binary_file if as_binary else system.read_entire_file
    return read_fn(filename)


def _write_file(filename : str, data : Union[str, bytes], as_binary : bool) -> None:
    """Wrapper around write_file or write_binary_file if AS_BINARY"""
    ## TODO2: allow for ignoring UTF-8 errors
    debug.trace(8, f"_write_file({filename}, _, {as_binary})")
    ## NOTE: maldito mypy is too picky
    ## TODO3: see if way to specify alternative union type that is accepted by it
    if as_binary and isinstance(data, bytes):
        system.write_binary_file(filename, data)
    else:
        system.write_file(filename, data)
    return


def old_download_web_document(url : str, filename: Optional[str] = None, download_dir : Optional[str] = None,
                              meta_hash : Optional[Dict[str, Any]] = None, use_cached : bool = False,
                              as_binary : bool = False, ignore : bool = False) -> OptStrBytes:
    """Download document contents at URL, returning as unicode text (unless AS_BINARY)
    Notes: An optional FILENAME can be given for the download, an optional DOWNLOAD_DIR[ectory] can be specified (defaults to '.'), and an optional META_HASH can be specified for recording filename and headers. Existing files will be considered if USE_CACHED. If IGNORE, no exceptions reports are printed."""
    # EX: ("Search" in old_download_web_document("https://www.google.com"))
    # EX: ((url := "https://simple.wikipedia.org/wiki/Dollar"), (old_download_web_document(url) == download_web_document(url)))[-1]
    debug.trace_fmtd(4, "old_download_web_document({u}, d={d}, f={f}, h={mh}, cached={uc}, binary={ab})",
                     u=url, d=download_dir, f=filename, mh=meta_hash,
                     uc=use_cached, ab=as_binary)

    # Download the document and optional headers (metadata).
    if url.endswith("/"):
        url = url[:-1]
    if filename is None:
        filename = system.quote_url_text(gh.basename(url))
        debug.trace_fmtd(5, "\tquoted filename: {f}", f=filename)
    if "//" not in url:
        url = "http://" + url
    if download_dir is None:
        download_dir = DOWNLOAD_DIR
    if (not system.file_exists(download_dir)):
        gh.full_mkdir(download_dir)
    local_filename = gh.form_path(download_dir, filename)
    ## TEST: headers = {}
    ## TEST: headers : Dict[Any, Any] = {}
    headers : HTTPMessage = HTTPMessage()
    status_code = DEFAULT_STATUS_CODE
    ok = False
    if DOWNLOAD_TIMEOUT:
        # HACK: set global socket timeout
        import socket                   # pylint: disable=import-error, import-outside-toplevel
        socket.setdefaulttimeout(DOWNLOAD_TIMEOUT)
    if use_cached and system.non_empty_file(local_filename):
        debug.trace_fmtd(5, "Using cached file for URL: {f}", f=local_filename)
    else:
        try:
            ## TEMP: issue separate call to get status code (TODO: figure out how to do after urlretrieve call)
            headers = {
                'User-Agent': USER_AGENT
            }
            # Create a Request with the URL and headers and then open the URL
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as fp:
                status_code = fp.getcode()
                content = fp.read()

            # Save the content to a local file
            _write_file(local_filename, content, as_binary)
            debug.trace_fmtd(5, "=> local file: {f}; headers={{{h}}}",
                             f=local_filename, h=headers)
            ok = True
        except(HTTPError) as exc:
            status_code = exc.code
        except:
            ## TODO: except(IOError, UnicodeError, URLError, socket.timeout):
            debug.reference_var(URLError)
            if not ignore:
                system.print_exception_info("old_download_web_document")
        # Optionally pause after accessing the URL (to avoid overloading the same server).
        if POST_DOWNLOAD_SLEEP_SECONDS:
            system.sleep(POST_DOWNLOAD_SLEEP_SECONDS, message="Post-download")
                
    if not ok:
        local_filename = ""
    if meta_hash is not None:
        meta_hash[FILENAME] = local_filename
        meta_hash[HEADERS] = headers
    debug.trace(5, f"status_code={status_code}")

    # Read all of the data and return as text
    data = _read_file(local_filename, as_binary) if local_filename else None
    debug.trace_fmtd(7, "old_download_web_document() => {d}", d=data)
    return data


def download_web_document(url : str, filename: Optional[str] = None, download_dir: Optional[str] = None, meta_hash=None, use_cached : bool = False, as_binary : bool = False, ignore : bool = False) -> OptStrBytes:
    """Download document contents at URL, returning as unicode text (unless AS_BINARY).
    Notes: An optional FILENAME can be given for the download, an optional DOWNLOAD_DIR[ectory] can be specified (defaults to 'downloads'), and an optional META_HASH can be specified for recording filename and headers. Existing files will be considered if USE_CACHED. If IGNORE, no exceptions reports are printed."""
    # EX: "currency" in download_web_document("https://simple.wikipedia.org/wiki/Dollar")
    # EX: download_web_document("www. bogus. url.html") => None
    ## TODO: def download_web_document(url, /, filename=None, download_dir=None, meta_hash=None, use_cached=False):
    ## TODO3: add user-agent
    debug.trace_fmtd(4, "download_web_document({u}, d={d}, f={f}, h={mh}, cached={uc}, binary={ab})",
                     u=url, d=download_dir, f=filename, mh=meta_hash,
                     uc=use_cached, ab=as_binary)
    if not DOWNLOAD_VIA_REQUESTS:
        return old_download_web_document(url, filename, download_dir, meta_hash, use_cached, as_binary, ignore=ignore)
    
    # Download the document and optional headers (metadata).
    if url.endswith("/"):
        url = url[:-1]
    if filename is None:
        ## TODO: support local filenames with subdirectories
        filename = system.quote_url_text(gh.basename(url))
        debug.trace_fmtd(5, "\tquoted filename: {f}", f=filename)
    if "//" not in url:
        url = "http://" + url
    if download_dir is None:
        download_dir = DOWNLOAD_DIR
    if not gh.is_directory(download_dir):
        gh.full_mkdir(download_dir)
    local_filename = gh.form_path(download_dir, filename)
    if meta_hash is not None:
        meta_hash[FILENAME] = local_filename
    doc_data: OptStrBytes = ""
    if use_cached and system.non_empty_file(local_filename):
        debug.trace_fmtd(5, "Using cached file for URL: {f}", f=local_filename)
        doc_data = _read_file(local_filename, as_binary)
    else:
        doc_data = retrieve_web_document(url, meta_hash=meta_hash, as_binary=as_binary, ignore=ignore)
        if doc_data:
            _write_file(local_filename, doc_data, as_binary)
    debug.trace_expr(5, local_filename, meta_hash)

    ## TODO: show hex dump of initial data
    debug.trace_fmtd(6, "download_web_document() => _; len(_)={l}",
                     l=(len(doc_data) if doc_data else -1))
    return doc_data


def test_download_html_document(url : str, encoding : Optional[str] = None, lookahead: int = 256, **kwargs) -> OptStrBytes:
    """Wrapper around download_web_document for HTML or text (i.e., non-binary), using ENCODING.
    Note: If ENCODING unspecified, checks result LOOKAHEAD bytes for meta encoding spec and uses UTF-8 as a fallback."""
    # EX: "Google" in test_download_html_document("www.google.com")
    ## bad-EX: "Tomás" not in test_download_html_document("http://www.tomasohara.trade", encoding="big5"¨)
    # EX: "Tomás" not in test_download_html_document("http://www.tomasohara.trade", encoding="big5")
    result = (download_web_document(url, as_binary=True, **kwargs) or b"")
    ## TEMP: for mypy
    if isinstance(result, str):
        result = result.encode('utf-8')
    if (len(result) and (not encoding)):
        encoding = "UTF-8"
        if my_re.search(r"<meta.*charset=[\"\']?([^\"\' <>]+)[\"\']?", str(result[:lookahead])):
            encoding = my_re.group(1)
            debug.trace(5, f"Using {encoding} for encoding based on meta charset")
    try:
        if isinstance(result, bytes) and encoding:
            result = result.decode(encoding=encoding, errors='ignore')
    except:
        result = str(result)
        system.print_exception_info("download_html_document decode")
    debug.trace_fmtd(7, "test_download_html_document({u}, [enc={e}, lkahd={la}]) => {r}; len(_)={l}",
                     u=url, e=encoding, la=lookahead, r=gh.elide(result), l=len(result))
    return (result)


def download_html_document(url : str, **kwargs) -> str:
    """Wrapper around download_web_document for HTML or text (i.e., non-binary)"""
    result : str = str(download_web_document(url, as_binary=False, **kwargs) or "")
    debug.trace_fmtd(7, "download_html_document({u}) => {r}; len(_)={l}",
                     u=url, r=gh.elide(result), l=len(result))
    return (result)


def download_binary_file(url : str, **kwargs) -> OptStrBytes:
    """Wrapper around download_web_document for binary files (e.g., images)"""
    result : OptStrBytes = (download_web_document(url, as_binary=True, **kwargs) or b"")
    debug.trace_fmtd(7, "download_binary_file({u}) => _; len(_)={l}",
                     u=url, l=(len(result) if result else 0))
    return (result)
    

def retrieve_web_document(url : str, meta_hash=None, as_binary : bool = False, ignore : bool = False) -> OptStrBytes:
    """Get document contents at URL, using unicode text (unless AS_BINARY)
    Note:
    - Simpler version of old_download_web_document, using an optional META_HASH for recording headers
    - Works around Error 403's presumably due to urllib's user agent
    - If IGNORE, no exceptions reports are printed."""
    # EX: bool(my_re.search("Scrappy.*Cito", retrieve_web_document("www.tomasohara.trade")))
    # Note: See https://stackoverflow.com/questions/34957748/http-error-403-forbidden-with-urlretrieve.
    debug.trace_fmtd(5, "retrieve_web_document({u})", u=url)
    ## TEST: result : Optional[AnyStr] = None
    result : Optional[Union[str, bytes]] = None
    status_code = DEFAULT_STATUS_CODE
    if "//" not in url:
        url = "http://" + url
    try:
        headers = {
            'User-Agent': USER_AGENT
        }
        r = requests.get(url, timeout=DOWNLOAD_TIMEOUT, headers=headers)
        status_code = r.status_code
        result = r.content
        debug.assertion(isinstance(result, bytes))
        if (isinstance(result, bytes) and not as_binary):
            result = result.decode(errors='ignore')
        if meta_hash is not None:
            meta_hash[HEADERS] = r.headers
    ## TODO: except(AttributeError, ConnectionError):
    except:
        if not ignore:
            system.print_exception_info("retrieve_web_document")
    # Optionally pause after accessing the URL (to avoid overloading the same server).
    if POST_DOWNLOAD_SLEEP_SECONDS:
        system.sleep(POST_DOWNLOAD_SLEEP_SECONDS, message="Post-download")
    debug.trace(5, f"status_code={status_code}")
    debug.trace_fmtd(7, "retrieve_web_document() => {r}", r=result)
    return result


def init_BeautifulSoup():
    """Make sure bs4.BeautifulSoup is loaded"""
    import bs4                           # pylint: disable=import-error, import-outside-toplevel
    global BeautifulSoup
    BeautifulSoup = bs4.BeautifulSoup
    return


def extract_html_link(html_text : str, url : Optional[str] = None, base_url : Optional[str] = None):
    """Returns list of all aref links in HTML. The optional URL and BASE_URL parameters can be specified to ensure the link is fully resolved."""
    debug.trace_fmtd(7, "extract_html_links(_):\n\thtml={h}", h=html_text)

    # Parse HTML, extract base URL if given and get website from URL.
    init_BeautifulSoup()
    soup = BeautifulSoup(html_text, 'html.parser') if BeautifulSoup else None
    web_site_url = ""
    if url:
        web_site_url = my_re.sub(r"(https?://[^\/]+)/?.*", r"\1", url)
        debug.trace_fmtd(6, "wsu1={wsu}", wsu=web_site_url)
        if not web_site_url.endswith("/"):
            web_site_url += "/"
            debug.trace_fmtd(6, "wsu2={wsu}", wsu=web_site_url)
    # Determine base URL
    if base_url is None and soup:
        base_url_info = soup.find("base")
        
        base_url = base_url_info.get("href") if base_url_info else None
        debug.trace_fmtd(6, "bu1={bu}", bu=base_url)
        if url and not base_url:
            # Remove parts of the URLafter the final slash
            base_url = my_re.sub(r"(^.*/[^\/]+/)[^\/]+$", r"\1", url)
            debug.trace_fmtd(6, "bu2={bu}", bu=base_url)
        if web_site_url and not base_url:
            base_url = web_site_url
            debug.trace_fmtd(6, "bu3={bu}", bu=base_url)
        if base_url and not base_url.endswith("/"):
            base_url += "/"
            debug.trace_fmtd(6, "bu4={bu}", bu=base_url)

    # Get links and resolve to full URL (TODO: see if utility for this)
    links = []
    all_links = soup.find_all('a') if soup else []
    for link in all_links:
        debug.trace_fmtd(6, "link={inf}; style={sty}", inf=link, sty=link.attrs.get('style'))
        link_src = link.get("href", "")
        if not link_src:
            debug.trace_fmt(5, "Ignoring link without href: {img}", img=link)
            continue
        if link_src.startswith("/"):
            link_src = web_site_url + link_src
        elif base_url and not link_src.startswith("http"):
            link_src = base_url + "/" + link_src
        # Apply special case fixups (e.g., extraneous slashes)
        if my_re.search(r"(^.*://.*/)/(.*)", link_src):
            debug.trace(4, "FYI: Fixing up extract_html_link link: {link_src!r}")
            link_src = my_re.group(1) + my_re.group(2)
        links.append(link_src)
    debug.trace_fmtd(6, "extract_html_links() => {i}", i=links)
    return links


def format_checkbox(param_name : str, label : Optional[str] = None, skip_capitalize: Optional[bool] = None, default_value : OptBoolStr = False, disabled : bool = False, style : Optional[str] = None, misc_attr : Optional[str] = None, tooltip : Optional[str] = None, outer_span_class: Optional[str] = None, concat_label: Optional[bool] = None, skip_hidden: Optional[str] = None, on_change: Optional[str] = None, param_dict : Optional[Dict] = None) -> str:
    """Returns HTML specification for input checkbox with URL PARAM_NAME, optionally with LABEL, SKIP_CAPITALIZE, DEFAULT_VALUE, DISABLED, (CSS) STYLE, MISC_ATTR (catch all), TOOLTIP, OUTER_SPAN_CLASS, CONCAT_LABEL, SKIP_HIDDEN, ON_CHANGE, and PARAM_DICT.
    Note:
    - param_name + "-id" is used for the field ID.
    - The TOOLTIP requires CSS support (e.g., tooltip-control class).
    - See format_input_field for OUTER_SPAN_CLASS usage.
    - With CONCAT_LABEL, no space is added after the label.
    - ON_CHANGE specifies JavaScript to execute when values changes.
    Warning: includes separate hidden field for explicit off state unless SKIP_HIDDEN.
    """
    ## Note: Checkbox values are only submitted if checked, so a hidden field is used to provide explicit off.
    ## This requires use of fix_url_parameters to give preference to final value specified (see results.mako).
    ## See https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/checkbox for hidden field tip.
    ## Also see https://stackoverflow.com/questions/155291/can-html-checkboxes-be-set-to-readonly
    ## EX: format_checkbox("disable-touch") => "<input type='hidden' name='disable-touch' value='off'><label id='disable-touch-label-id' >Disable touch?&nbsp;<input type='checkbox' id='disable-touch-id' name='disable-touch'   ></label>"
    ## TODO3: add on_cange as with format_input_field
    debug.trace_expr(7, param_name, label, skip_capitalize, default_value, disabled, style,
                     misc_attr, tooltip, outer_span_class, concat_label, skip_hidden, on_change, param_dict,
                     prefix="in format_checkbox: ")
    checkbox_spec = get_url_param_checkbox_spec(param_name, default_value,
                                                param_dict=param_dict)
    disabled_spec = ("disabled" if disabled else "")
    status_spec = f"{checkbox_spec} {disabled_spec}".strip()
    style_spec = (f"style='{style}'" if style else "")
    misc_spec = (misc_attr if misc_attr else "")
    debug.assertion("'" not in str(on_change))
    misc_spec += (f" onchange=\"{on_change}\"" if on_change else "")
    label_misc_spec = ""
    if (label is None):
        label = (param_name.replace("-", " ") + "?")
        if not skip_capitalize:
            label = label.capitalize()
    ## TODO: use hidden only if (default_value in ["1", "on", True])???
    result = ""
    if outer_span_class:
        result += f"<span class='{outer_span_class}'>"
    if not skip_hidden:
        result += f"<input type='hidden' name='{param_name}' value='off'>"
    tooltip_start_spec = tooltip_end_spec = ""
    if tooltip:
        if TARGET_BOOTSTRAP:
            spec = f" data-bs-toggle='tooltip' title='{tooltip}'"
            misc_spec += spec
            label_misc_spec += spec
        else:
            tooltip_start_spec = f'<span class="tooltip-control"><span class="tooltip-field">{tooltip}</span>'
            tooltip_end_spec = "</span>"
    result += f"<label id='{param_name}-label-id' {label_misc_spec}>{tooltip_start_spec}{label}{tooltip_end_spec}"
    if not concat_label:
        result += '&nbsp;'
    result += f"<input type='checkbox' id='{param_name}-id' name='{param_name}' {style_spec} {status_spec} {misc_spec}></label>"
    if outer_span_class:
        result += "</span>"
    debug.trace(6, f"format_checkbox({param_name}, ...) => {result}")
    return result
#
# EX: format_checkbox("disable-touch", skip_hidden=True, disabled=True) => "<label id='disable-touch-label-id' >Disable touch?&nbsp;<input type='checkbox' id='disable-touch-id' name='disable-touch'  disabled ></label>"


def format_url_param(name : str, default : Optional[str] = None):
    """Return URL parameter NAME formatted for an HTML form (e.g., escaped)"""
    # EX: set_param_dict({"q": '"hot dog"'}); format_url_param("q") => '&quot;hot dog&quot;'
    if default is None:
        default = ""
    value_spec = (get_url_param(name) or default)
    if value_spec:
        value_spec = escape_html_text(value_spec)
    debug.trace(5, f"format_url_param({name}) => {value_spec!r}")
    return value_spec
#
# EX: format_url_param("r") => ""
# EX: format_url_param("r", default="R") => "R"


def format_input_field(
        param_name : str, label: Optional[str] = None, skip_capitalize=None,
        default_value: Optional[str] = None, max_len : Optional[int] = None,
        size : Optional[int] = None, max_value : Optional[int] = None, disabled : Optional[int] = None,
        style: Optional[str] = None, misc_attr: Optional[str] = None,
        tooltip: Optional[str] = None, text_area: Optional[bool] = None,
        num_rows : Optional[int] = None, on_change: Optional[str] = None, on_input: Optional[str] = None,
        field_type: Optional[str] = None, concat_label: Optional[bool] = None,
        outer_span_class: Optional[str] = None, param_dict : Optional[Dict] = None):
    """Returns HTML specification for input field with URL PARAM_NAME, optionally with LABEL, SKIP_CAPITALIZE, DEFAULT_VALUE, MAX_LEN, SIZE, MAX_VALUE, DISABLED, (CSS) STYLE, MISC_ATTR (catch all), TOOLTIP, NUM_ROWS, ON_CHANGE, FIELD_TYPE, CONCAT_LABEL, OUTER_SPAN_CLASS, and PARAM_DICT.
    Note:
    - param_name + "-id" is used for the field ID.
    - SIZE should be specified if not same as MAX_LEN.
    - MAX_VALUE is for number fields.
    - ON_INPUT specifies JavaScript to execute when values changes.
    - ON_CHANGE is similar but waits for item to loose focus
    - See format_checkbox for TOOLTIP notes.
    - With CONCAT_LABEL, no space is added after the label.
    - With OUTER_SPAN_CLASS the input field is wrapped in <span> with given class for styling
      (e.g., "display: inline-block; white-space: nowrap;" to keep field and label together).
    """
    # EX: format_input_field("quest") => '<label id=\'quest-label-id\' >Quest&nbsp;<input id="quest-id"  name="quest"     ></label>'
    # TODO2: doscument tooltip usage & add option for css classes involved (better if done via class-based interface).
    # TODO3: max_len => maxlength; make sure single quote used for attribute consistently (likewise elsewhere)
    # Note: See https://stackoverflow.com/questions/25247565/difference-between-maxlength-size-attribute-in-html
    # For tooltip support, see https://stackoverflow.com/questions/65854934/is-a-css-only-inline-tooltip-with-html-content-inside-eg-images-possible.
    debug.trace_expr(7, param_name, label, skip_capitalize, default_value, max_len, size, max_value,
                     disabled, style, misc_attr, tooltip, text_area, num_rows, on_change,
                     field_type, concat_label, outer_span_class, param_dict,
                     prefix="in format_input_field: ")
    if (label is None):
        label = param_name.replace("-", " ")
        if not skip_capitalize:
            label = label.capitalize()
    if (default_value is None):
        default_value = ""
    if not isinstance(default_value, str):
        debug.trace(5, f"FYI: Use string for {param_name} default {default_value!r}")
        default_value = str(default_value)        
    if (num_rows is None):
        num_rows = 1
    if (size is None):
        size = max_len
    type_spec = (f"type='{field_type}'" if field_type else "")
    field_value = (get_url_parameter_value(param_name, param_dict=param_dict) or default_value)
    ## TEST: value_spec = (f"value='{field_value}'" if field_value else "")
    value_spec = (f"value='{escape_html_text(field_value)}'" if field_value else "")
    disabled_spec = ("disabled" if disabled else "")
    style_spec = (f"style='{style}'" if style else "")
    misc_spec = (misc_attr if misc_attr else "")
    debug.assertion("'" not in str(on_change))
    misc_spec += (f" onchange=\"{on_change}\"" if on_change else "")
    debug.assertion("'" not in str(on_input))
    misc_spec += (f" oninput=\"{on_input}\"" if on_input else "")
    label_misc_spec = ""
    tooltip_start_spec = tooltip_end_spec = ""
    if tooltip:
        if TARGET_BOOTSTRAP:
            spec = f" data-bs-toggle='tooltip' title='{tooltip}'"
            misc_spec += spec
            label_misc_spec += spec
        else:
            tooltip_start_spec = f'<span class="tooltip-control"><span class="tooltip-field">{tooltip}</span>'
            tooltip_end_spec = "</span>"
    result = ""
    if outer_span_class:
        result += f"<span class='{outer_span_class}'>"
    result += f"<label id='{param_name}-label-id' {label_misc_spec}>{tooltip_start_spec}{label}{tooltip_end_spec}"
    if not concat_label:
        result += '&nbsp;'
    if text_area:
        debug.assertion(not type_spec)
        max_len_spec = (f'maxlength="{max_len}"' if max_len else "")
        value_spec = format_url_param(param_name)
        result += f'<textarea id="{param_name}-id" name="{param_name}" rows={num_rows} {style_spec} {max_len_spec} {disabled_spec} {misc_spec}>{value_spec}</textarea>'
    else:
        len_spec = ""
        if max_len:
            len_spec += f' maxlength="{max_len}"'
        if size:
            len_spec += f' size="{size}"'
        if max_value:
            debug.assertion(field_type == "number")
            len_spec += f' max="{max_value}"'
        result += f'<input id="{param_name}-id" {value_spec} name="{param_name}" {style_spec} {len_spec} {disabled_spec} {misc_spec} {type_spec}>'
    result += "</label>"
    if outer_span_class:
        result += "</span>"
        
    debug.trace(6, f"format_input_field({param_name}, ...) => {result!r}")
    return result
#
# EX: format_input_field("quest", default_value="O'What?") => '<label id=\'quest-label-id\' >Quest&nbsp;<input id="quest-id" value=\'O&#x27;What?\' name="quest"     ></label>'
# EX: format_input_field("num-id", label="Num", max_value=101, field_type="number") => '<label id=\'num-id-label-id\' >Num&nbsp;<input id="num-id-id"  name="num-id"   max="101"   type=\'number\'></label>'

#-------------------------------------------------------------------------------
# TEMP: Code previously in other modules
# TODO3: move above according to some logical grouping

def escape_html_text(text : str):
    """Add entity encoding to TEXT to make suitable for HTML"""
    # Note: This is wrapper around html.escape and just handles '&', '<', '>', "'", and '"'.
    # EX: escape_html_text("<2/") => "&lt;2/"
    # EX: escape_html_text("Joe's hat") => "Joe&#x27;s hat"
    debug.trace_fmtd(8, "in escape_html_text({t})", t=text)
    result = html.escape(text)
    debug.trace_fmtd(7, "out escape_html_text({t}) => {r}", t=text, r=result)
    return result
#
escape_html_value = escape_html_text

def unescape_html_text(text : str):
    """Remove entity encoding, etc. from TEXT (i.e., undo)"""
    # Note: This is wrapper around html.unescape
    # See https://stackoverflow.com/questions/21342549/unescaping-html-with-special-characters-in-python-2-7-3-raspberry-pi.
    # EX: unescape_html_text("&lt;2/") => "<2/"
    # EX: unescape_html_text("Joe&#x27;s hat") => "Joe's hat"
    debug.trace_fmtd(8, "in unescape_html_text({t})", t=text)
    result = ""
    result = html.unescape(text)
    debug.trace_fmtd(7, "out unescape_html_text({t}) => {r}", t=text, r=result)
    return result
#
unescape_html_value = unescape_html_text


def html_to_text(document_data : str):
    """Returns text version of html DATA"""
    # EX: html_to_text("<html><body><!-- a cautionary tale -->\nMy <b>fat</b> dog has fleas</body></html>") => '\nMy  fat  dog has fleas'
    # Note: stripping javascript and style sections based on following:
    #   https://stackoverflow.com/questions/22799990/beatifulsoup4-get-text-still-has-javascript
    debug.trace_fmtd(7, "html_to_text(_):\n\tdata={d}", d=document_data)
    init_BeautifulSoup()
    soup = BeautifulSoup(document_data, "lxml") if BeautifulSoup else None
    # Remove all script and style elements
    text = ""
    if soup:
        for script in soup.find_all(["script", "style"]):
            # *** TODO: soup = soup.extract(script)
            # -or- Note the in-place change (i.e., destructive).
            script.extract()
        # Get the text
        text = soup.get_text(separator=" ")
    debug.trace_fmtd(6, "html_to_text() => {t}", t=gh.elide(text))
    return text


def extract_html_images(document_data : OptStrBytes = None, url : Optional[str] = None, filename : Optional[str] = None):
    """Returns list of all images in HTML DOC from URL (n.b., URL used to determine base URL)"""
    debug.trace(6, f"extract_html_images(_, {url}, fn={filename})")
    debug.trace_fmtd(8, "\tdata={d}", d=document_data)
    # TODO: add example; return dimensions
    # TODO: have URL default to current directory
    debug.assertion(document_data or url or filename)
    if (document_data is None):
        if (filename is not None):
            document_data = system.read_file(filename)
        elif (url is not None):
            document_data = download_web_document(url)
        else:
            system.print_error("Error in extract_html_images: unable to get data without URL or filename")
    if url is None:
        url = ""

    # Parse HTML, extract base URL if given and get website from URL.
    init_BeautifulSoup()
    soup = BeautifulSoup(document_data, 'html.parser') if BeautifulSoup else None
    web_site_url = my_re.sub(r"(https?://[^\/]+)/?.*", r"\1", url)
    debug.trace_fmtd(6, "wsu1={wsu}", wsu=web_site_url)
    if not web_site_url.endswith("/"):
        web_site_url += "/"
        debug.trace_fmtd(6, "wsu2={wsu}", wsu=web_site_url)
    base_url_info = soup.find("base") if soup else None
    base_url = base_url_info.get("href") if base_url_info else None
    debug.trace_fmtd(6, "bu1={bu}", bu=base_url)
    if not base_url:
        base_url = web_site_url
        debug.trace_fmtd(6, "bu3={bu}", bu=base_url)
    if not base_url.endswith("/"):
        base_url += "/"
        debug.trace_fmtd(6, "bu4={bu}", bu=base_url)

    # Get images and resolve to full URL (TODO: see if utility for this)
    # TODO: include CSS background images
    # TODO: use DATA-SRC if SRC not valid URL (e.g., src="data:image/gif;base64,R0lGODl...")
    images = []
    all_images = soup.find_all('img') if soup else []
    for image in all_images:
        debug.trace_fmtd(6, "image={inf}; style={sty}", inf=image, sty=image.attrs.get('style'))
        ## TEST: if (image.has_attr('attrs') and (image.attrs.get['style'] in ["display:none", "visibility:hidden"])):
        if (image.attrs.get('style') in ["display:none", "visibility:hidden"]):
            debug.trace_fmt(5, "Ignoring hidden image: {img}", img=image)
            continue
        image_src = image.get("src", "")
        if not image_src:
            debug.trace_fmt(5, "Ignoring image without src: {img}", img=image)
            continue
        if image_src.startswith("//"):
            url_proto = (my_re.search(r"^(\w+):", url) and my_re.group(1))
            image_src = f"{url_proto}:{image_src}"
        elif not my_re.search(r"^(http)|(data:)", image_src):
            image_src = base_url + image_src.lstrip("/")
        else:
            debug.trace(7, f"Using image src as is: {image_src}")
        ## TEMP: fixup for trailing newline (TODO: handle upstream)
        image_src = image_src.strip()
        if image_src not in images:
            images.append(image_src)
    debug.trace_fmtd(6, "extract_html_images() => {i}", i=images)
    return images


def format_html_message(title, text=None):
    """Format text as HTML doc (e.g., for errors)
    Note: TITLE is shown in browser title as well as h3 in body.
    Optional TEXT is shown as regular text.
    """
    title_escaped = escape_html_text(title)
    text_escaped = escape_html_text(text) if text else ""
    result = ("<html lang='en'>" +
              "  <head>" +
              f"    <title>{title_escaped}</title>" +
              "  </head>" +
              "  <body>" +
              f"    <h3>{title_escaped}<h3>" +
              f"    {text_escaped}" +
              "  </body>" +
              "</html>")
    return result
#
# EX: format_html_message("key") => "<html lang='en'>  <head>    <title>hey</title>  </head>  <body>    <h3>hey<h3>      </body></html>"

#-------------------------------------------------------------------------------

def main(args : List[str]) -> None:
    """Supporting code for command-line processing"""
    ## NOTE: This is work-in-progress from a debug-only utility
    debug.trace_fmtd(6, "main({a})", a=args)

    # Parse command line arguments
    # TODO2: use master.Main for arg parsing
    plain_text = False
    plain_html = False
    show_usage = False
    use_stdout = False
    use_inner = True
    take_snapshot = False
    console_log = False
    pause_at_end = False
    quiet = False
    verbose = False
    debug_hooks = False
    filename : Optional[str] = None
    for i, arg in enumerate(args[1:]):
        if (arg == "--help"):
            show_usage = True
        elif (arg == "--regular"):
            plain_text = True
            use_inner = False
        elif (arg == "--html"):
            plain_html = True
        elif (arg == "--text"):
            plain_html = False
            use_inner = True
        elif (arg == "--inner"):
            use_inner = True
        elif (arg == "--snapshot"):
            take_snapshot = True
        elif (arg == "--console-log"):
            console_log = True
        elif (arg == "--pause"):
            pause_at_end = True
        elif (arg == "--stdout"):
            use_stdout = True
        elif (arg == "--quiet"):
            quiet = True
        elif (arg == "--verbose"):
            verbose = True
        elif (arg == "--debug"):
            debug_hooks = True
        elif (not arg.startswith("-")):
            filename = arg
            break
        else:
            system.print_stderr(f"Error: unknown argument: {arg}")
            show_usage = True
            break
        i += 1

    # HACK: Convert local html document to text
    if (filename and (not my_re.search("www|http|file:", filename) or plain_text)):
        debug.assertion(not use_inner)
        doc_filename = filename
        document_data = system.read_file(doc_filename)
        document_text = html_to_text(document_data)
        if use_stdout:
            print(document_text)
        else:
            system.write_file(doc_filename + ".list", document_text)
            print(f"See {doc_filename}.list")

    # HACK: Do simple test of inner-HTML support
    # TODO: Do simpler test of download_web_document
    # TODO1: add explicit argument for inner-html support
    elif (filename):
        # Get web page text
        debug.trace_fmt(6, "browser_cache: {bc}", bc=browser_cache)
        url = filename
        ## TODO3: make the debug-level-based processing more explicit
        USUAL_DEBUGGING = debug_hooks and debug.debugging()
        VERBOSE_DEBUGGING = debug_hooks and debug.debugging(TL.VERBOSE)
        QUITE_VERBOSE_DEBUGGING = debug_hooks and debug.debugging(TL.QUITE_VERBOSE)
        alt_html_data: OptStrBytes = None
        if QUITE_VERBOSE_DEBUGGING:
            alt_html_data = retrieve_web_document(url) or ""
            debug.trace_expr(1, alt_html_data, max_len=32768)
        html_data: OptStrBytes = None
        if plain_html or VERBOSE_DEBUGGING:
            html_data = download_web_document(url) or ""
            if (isinstance(html_data, str) and isinstance(alt_html_data, str)):
                debug.trace_expr(TL.VERBOSE, html_data, max_len=32768)
                debug.assertion(system.relative_intersection(alt_html_data.split(),
                                                             html_data.split()) > 0.9)
        base_filename = system.quote_url_text(url)
        if not base_filename:
            base_filename = "output.html"
        if not base_filename.endswith(".html"):
            base_filename += ".html"
        filename = gh.form_path(DOWNLOAD_DIR, base_filename, create=True)
        basename = gh.remove_extension(filename, ".html")

        if plain_html:
            if use_stdout:
                print(html_data)
            else:
                system.write_file(filename, html_data)
                print(f"See {filename!r} for regular HTML.")
        else:
            debug.assertion(use_inner)
            if USUAL_DEBUGGING:
                out_path = write_temp_file("pre-" + base_filename, html_data or "")
                debug.trace(1, f"See {out_path!r} for non-inner HTML")

            # Show inner/outer HTML
            browser = get_browser(url)
            rendered_html = get_inner_html(url, browser=browser)
            output_filename = "post-" + base_filename
            out_path = ""
            output_to_file = (not use_stdout) or USUAL_DEBUGGING
            if output_to_file:
                output_dir = DOWNLOAD_DIR if (not use_stdout) else None
                out_path = write_temp_file(output_filename, rendered_html,
                                           temp_dir=output_dir)
            if use_stdout:
                if not quiet:
                    print("Rendered html:")
                print(system.to_utf8(rendered_html))            
            else:
                print(f"See {out_path!r} for inner HTML")
            if take_snapshot:
                browser.get_screenshot_as_file(f"{basename}.png")
                print(f"Snapshot: {basename}.png")
            if console_log:
                log_contents = browser.get_log('browser')
                system.write_file(f"{basename}.console.log", log_contents)
                print(f"Console log: {basename}.console.log")

            if USUAL_DEBUGGING:
                ## TODO3: isolate for use as main output
                rendered_text = get_inner_text(url, browser=browser)
                debug.trace_fmt(5, "type(rendered_text): {t}", t=rendered_text)
                output_filename = "post-" + base_filename + ".txt"
                out_path = write_temp_file(output_filename, rendered_text)
                debug.trace(1, f"See {out_path!r} for inner text")
            debug.trace_fmt(4, "browser_cache: {bc}", bc=browser_cache)

            # Wait for user and then quit browser
            if pause_at_end:
                system.print_error("Press enter to proceed")
                sys.stdin.readline()
            shutdown_browser(browser)
    else:
        show_usage = True

    # Show usage if user not sure what to do or invalid option.
    ## TODO3: rework via Main class (see summarize_pytest.py).
    # 
    if show_usage:
        script = gh.basename(__file__)
        print(f"Usage: {script} [--help] [misc] [[--regular | [--inner [--snapshot] [--pause]] | --html] [filename]]")
        print("   misc: [--verbose] [--stdout] [--quiet] [--debug]")
        print()
        print("Notes:")
        print("- Specify a local HTML file to download (e.g., save as text).")
        print("- Otherwise, specify a URL for a simple test of inner html access (n.b., via stdout).")
        print("- Use --regular to bypass default inner processing (and save as text).")
        ## TODO3: add explicit option like --text to make processing more consistent
        print("- With --html or --inner, the result is saved as html.")
        print("- The --inner option involves JavaScript access via selenium.")
        print("- Some options controlled by environment variables (e.g., TMPDIR).")
        print("- Use HEADLESS_WEBDRIVER=0 ... to show the browser during the download.")
        print(f"- Additional output produced when DEBUG_LEVEL is {TL.USUAL} or higher.")
        if verbose:
            INDENT = "    "
            env_opts = system.formatted_environment_option_descriptions(sort=True, indent=INDENT)
            print(f"- Other env. options:\n{INDENT}{env_opts}")
        else:
            print("- Use --verbose to see other env. options.")
        print("- Use --debug for sanity checks.")
            
        print()
        print("Examples:")
        print(f"- {script} --inner --stdout --quiet https://x.com/home > x-home.html")
        print(f"- {script} --regular --stdout bootstrap-hello-world.html > bootstrap-hello-world.txt")
    return

if __name__ == '__main__':
    main(sys.argv)
