#! /usr/bin/env python
#
# Micellaneous HTML utility functions, in particular with support for resolving
# HTML rendered via JavaScript. This was motivated by the desire to extract
# images from pubchem.ncbi.nlm.nih.gov web pages for drugs (e.g., Ibuprofen,
# as illustrated below).
#
#-------------------------------------------------------------------------------
# Example usage:
#
# TODO: see what html_file should be set to
# $ PATH="$PATH:/usr/local/programs/selenium" DEBUG_LEVEL=6 MOZ_HEADLESS=1 $PYTHON html_utils.py "$html_file" > _html-utils-pubchem-ibuprofen.log7 2>&
# $ cd $TMPDIR
# $ wc *ibuprofen*
#     13   65337  954268 post-https%3A%2F%2Fpubchem.ncbi.nlm.nih.gov%2Fcompound%2FIbuprofen
#   3973   24689  178909 post-https%3A%2F%2Fpubchem.ncbi.nlm.nih.gov%2Fcompound%2FIbuprofen.txt
#     60    1152   48221 pre-https%3A%2F%2Fpubchem.ncbi.nlm.nih.gov%2Fcompound%2FIbuprofen
#
# $ count_it.perl "<img" pre-https%3A%2F%2Fpubchem.ncbi.nlm.nih.gov%2Fcompound%2FIbuprofen
# $ count_it.perl "<img" post-https%3A%2F%2Fpubchem.ncbi.nlm.nih.gov%2Fcompound%2FIbuprofen
# <img	7
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
#-------------------------------------------------------------------------------
# TODO:
# - Standardize naming convention for URL parameter accessors (e.g., get_url_param vs. get_url_parameter).
# 

"""HTML utility functions"""

# Standard packages
import re
import sys
import time
import urllib
from urllib.error import HTTPError, URLError

# Installed packages
# Note: selenium import now optional; BeautifulSoup also optional
## OLD: from selenium import webdriver
import requests

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system

# Constants
DEFAULT_STATUS_CODE = "000"
MAX_DOWNLOAD_TIME = system.getenv_integer("MAX_DOWNLOAD_TIME", 60)
MID_DOWNLOAD_SLEEP_SECONDS = system.getenv_integer("MID_DOWNLOAD_SLEEP_SECONDS", 60)
POST_DOWNLOAD_SLEEP_SECONDS = system.getenv_integer("POST_DOWNLOAD_SLEEP_SECONDS", 0)
SKIP_BROWSER_CACHE = system.getenv_boolean("SKIP_BROWSER_CACHE", False)
USE_BROWSER_CACHE = (not SKIP_BROWSER_CACHE)
DOWNLOAD_VIA_URLLIB = system.getenv_bool("DOWNLOAD_VIA_URLLIB", False)
DOWNLOAD_VIA_REQUESTS = (not DOWNLOAD_VIA_URLLIB)

# Globals
# note: for convenience in Mako template code
user_parameters = {}

# Placeholders for dynamically loaded modules
BeautifulSoup = None

#-------------------------------------------------------------------------------
# Helper functions (TODO, put in system.py)

TEMP_DIR = system.getenv_text("TMPDIR", "/tmp")
#
def write_temp_file(filename, text):
    """Create FILENAME in temp. directory using TEXT"""
    temp_path = system.form_path(TEMP_DIR, filename)
    system.write_file(temp_path, text)
    return

#-------------------------------------------------------------------------------
# HTML utility functions

browser_cache = {}
##
def get_browser(url):
    """Get existing browser for URL or create new one
    Note: This is for use in web automation (e.g., via selenium).
    """
    browser = None
    global browser_cache
    # Check for cached version of browser. If none, create one and access page.
    browser = browser_cache.get(url) if USE_BROWSER_CACHE else None
    if not browser:
        # HACK: unclean import (i.e., buried in function)
        from selenium import webdriver       # pylint: disable=import-error, import-outside-toplevel
        browser = webdriver.Firefox()
        if USE_BROWSER_CACHE:
            browser_cache[url] = browser
        browser.get(url)
        if POST_DOWNLOAD_SLEEP_SECONDS:
            time.sleep(POST_DOWNLOAD_SLEEP_SECONDS)
    # Make sure the bare minimum is included (i.e., "<body></body>"
    debug.assertion(len(browser.execute_script("return document.body.outerHTML")) > 13)
    debug.trace_fmt(5, "get_browser({u}) => {b}", u=url, b=browser)
    return browser


def get_inner_html(url):
    """Return the fully-rendered version of the URL HTML source (e.g., after JavaScript DOM manipulation"""
    # Based on https://stanford.edu/~mgorkove/cgi-bin/rpython_tutorials/Scraping_a_Webpage_Rendered_by_Javascript_Using_Python.php
    # Navigate to the page (or get browser instance with existing page)
    browser = get_browser(url)
    # Wait for Javascript to finish processing
    wait_until_ready(url)
    # Extract fully-rendered HTML
    inner_html = browser.execute_script("return document.body.innerHTML")
    debug.trace_fmt(7, "get_inner_html({u}) => {h}", u=url, h=inner_html)
    return inner_html


def get_inner_text(url):
    """Get text of URL after JavaScript processing"""
    # See https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/innerText
    # Navigate to the page (or get browser instance with existing page)
    browser = get_browser(url)
    # Wait for Javascript to finish processing
    wait_until_ready(url)
    # Extract fully-rendered text
    inner_text = browser.execute_script("return document.body.innerText")
    debug.trace_fmt(7, "get_inner_text({u}) => {it}", u=url, it=inner_text)
    return inner_text


def document_ready(url):
    """Determine whether document for URL has completed loading"""
    # See https://developer.mozilla.org/en-US/docs/Web/API/Document/readyState
    browser = get_browser(url)
    ready_state = browser.execute_script("return document.readyState")
    is_ready = (ready_state == "complete")
    debug.trace_fmt(6, "document_ready({u}) => {r}; state={s}",
                    u=url, r=is_ready, s=ready_state)
    return is_ready


def wait_until_ready(url):
    """Wait for document_ready (q.v.) and pause to allow loading to finish"""
    # TODO: make sure the sleep is proper way to pause
    debug.trace_fmt(5, "in wait_until_ready({u})", u=url)
    start_time = time.time()
    end_time = start_time + MAX_DOWNLOAD_TIME
    while ((start_time < end_time) and (not document_ready(url))):
        time.sleep(MID_DOWNLOAD_SLEEP_SECONDS)
        if (not document_ready(url)):
            debug.trace_fmt(5, "Warning: time out ({s} secs) in accessing URL '{u}')'", s=system.round_num(end_time - start_time, 1), u=url)        
    debug.trace_fmt(5, "out wait_until_ready(); elapsed={t}s",
                    t=(time.time() - start_time))
    return
    

def escape_html_value(value):
    """Escape VALUE for HTML embedding"""
    return system.escape_html_text(value)


def unescape_html_value(value):
    """Undo escaped VALUE for HTML embedding"""
    return system.unescape_html_text(value)


def escape_hash_value(hash_table, key):
    """Wrapper around escape_html_value for HASH_TABLE[KEY] (or "" if missing).
    Note: newlines are converted into <br>'s."""
    escaped_item_value = escape_html_value(hash_table.get(key, ""))
    escaped_value = escaped_item_value.replace("\n", "<br>")
    debug.trace_fmtd(7, "escape_hash_value({h}, {k}) => '{r}'", h=hash_table, k=key, r=escaped_value)
    return escaped_value


def get_param_dict(param_dict=None):
    """Returns parameter dict using PARAM_DICT if non-Null else USER_PARAMETERS
       Note: """
    return (param_dict if param_dict else user_parameters)


def set_param_dict(param_dict):
    """Sets global user_parameters to value of PARAM_DICT"""
    global user_parameters
    user_parameters = param_dict


def get_url_param(name, default_value="", param_dict=None):
    """Get value for NAME from PARAM_DICT (e.g., USER_PARAMETERS), using DEFAULT_VALUE (normally "").
    Note: It will be escaped for use in HTML."""
    param_dict = get_param_dict(param_dict)
    value = escape_html_value(param_dict.get(name, default_value))
    value = system.to_unicode(value)
    debug.trace_fmtd(4, "get_url_param({n}, [{d}]) => {v})",
                     n=name, d=default_value, v=value)
    return value
#
get_url_parameter = get_url_param


def get_url_param_checkbox_spec(name, default_value="", param_dict=None):
    """Get value of boolean parameters formatted for checkbox (i.e., 'checked' iff True or on) from PARAM_DICT"""
    # NOTE: 1 also treated as True
    # TODO: implement in terms of get_url_param
    param_dict = get_param_dict(param_dict)
    param_value = param_dict.get(name, default_value)
    param_value = system.to_unicode(param_value)
    ## OLD: value = "checked" if (param_value in [True, "on"]) else ""
    value = "checked" if (param_value in ["1", "on", True]) else ""
    debug.trace_fmtd(4, "get_url_param_checkbox_spec({n}, [{d}]) => {v})",
                     n=name, d=default_value, v=value)
    return value
#
get_url_parameter_checkbox_spec = get_url_param_checkbox_spec


def get_url_parameter_value(param, default_value=False, param_dict=None):
    """Get (last) value for PARAM in PARAM_DICT (or DEFAULT_VALUE)"""
    param_dict = get_param_dict(param_dict)
    result = param_dict.get(param, default_value)
    if isinstance(result, list):
        result = result[-1]
    return result


def get_url_parameter_bool(param, default_value=False, param_dict=None):
    """Get boolean value for PARAM from PARAM_DICT, with "on" treated as True. @note the hash defaults to user_parameters, and the default value is False"""
    # NOTE: "1" also treated on True
    # TODO: implement in terms of get_url_param
    ## OLD: result = (param_dict.get(param, default_value) in ["on", True])
    result = (get_url_parameter_value(param, default_value, param_dict)
              ## OLD: in ["on", True])
              in ["1", "on", True])
    ## HACK: result = ((system.to_unicode(param_dict.get(param, default_value))) in ["on", True])
    debug.trace_fmtd(4, "get_url_parameter_bool({p}, {dft}, _) => {r}",
                     p=param, dft=default_value, r=result)
    return result
#
get_url_param_bool = get_url_parameter_bool


def get_url_parameter_int(param, default_value=0, param_dict=None):
    """Get integer value for PARAM from PARAM_DICT.
    Note: the hash defaults to user_parameters, and the default value is 0"""
    result = system.to_int(get_url_parameter_value(param, default_value, param_dict))
    debug.trace_fmtd(4, "get_url_parameter_int({p}, {dft}, _) => {r}",
                     p=param, dft=default_value, r=result)
    return result
#
get_url_param_int = get_url_parameter_int


def fix_url_parameters(url_parameters):
    """Use the last values for any user parameter with multiple values"""
    # EX: fix_url_parameters({'w':[7, 8], 'h':10}) => {'w':8, 'h':10}
    new_url_parameters = {p:(v[-1] if isinstance(v, list) else v) for (p, v) in url_parameters.items()}
    debug.trace_fmt(6, "fix_url_parameters({up}) => {new}",
                    up=url_parameters, new=new_url_parameters)
    return new_url_parameters

def download_web_document(url, filename=None, download_dir=None, meta_hash=None, use_cached=False):
    """Download document contents at URL, returning as unicode text. An optional FILENAME can be given for the download, an optional DOWNLOAD_DIR[ectory] can be specified (defaults to '.'), and an optional META_HASH can be specified for recording filename and headers. Existing files will be considered if USE_CACHED."""
    # EX: "currency" in download_web_document("https://simple.wikipedia.org/wiki/Dollar")
    # EX: download_web_document("www. bogus. url.html") => None
    ## TODO: def download_web_document(url, /, filename=None, download_dir=None, meta_hash=None, use_cached=False):
    debug.trace_fmtd(4, "download_web_document({u}, d={d}, f={f}, h={mh})",
                     u=url, d=download_dir, f=filename, mh=meta_hash)

    # Download the document and optional headers (metadata).
    # Note: urlretrieve chokes on URLS like www.cssny.org without the protocol.
    # TODO: report as bug if not fixed in Python 3
    if url.endswith("/"):
        url = url[:-1]
    if filename is None:
        ## TODO: support local filenames with subdirectories
        filename = system.quote_url_text(gh.basename(url))
        debug.trace_fmtd(5, "\tquoted filename: {f}", f=filename)
    if "//" not in url:
        url = "http://" + url
    if download_dir is None:
        download_dir = "downloads"
    if not gh.is_directory(download_dir):
        gh.full_mkdir(download_dir)
    local_filename = gh.form_path(download_dir, filename)
    if meta_hash is not None:
        meta_hash["filename"] = local_filename
    headers = ""
    status_code = DEFAULT_STATUS_CODE
    if use_cached and system.non_empty_file(local_filename):
        debug.trace_fmtd(5, "Using cached file for URL: {f}", f=local_filename)
    elif DOWNLOAD_VIA_REQUESTS:
        doc_data = retrieve_web_document(url, meta_hash=meta_hash)
        if doc_data:
            system.write_file(local_filename, doc_data)
    else:
        # TODO: put urllib-based support in separate function (e.g., old_retrieve_web_document)
        try:
            ## TEMP: issue separate call to get status code (TODO: figure out how to do after urlretrieve call)
            with urllib.request.urlopen(url) as fp:
                status_code = fp.getcode()
            local_filename, headers = urllib.request.urlretrieve(url, local_filename)      # pylint: disable=no-member

            # Read all of the data and return as text
            doc_data = system.read_entire_file(local_filename) if local_filename else None
        except(IOError, UnicodeError, URLError, HTTPError) as exc:
            ## TEST: debug.assertion(exc == system.get_exception())
            ## debug.trace_expr(5, exc, system.get_exception())
            ## DEBUG: debug.trace_object(5, exc, max_depth=2)
            local_filename = None
            stack = (type(exc) not in [HTTPError])
            system.print_exception_info("download_web_document", show_stack=stack)
            status_code = getattr(exc, "code", status_code)
        debug.trace(5, f"status_code={status_code}")
    if meta_hash is not None:
        meta_hash["headers"] = headers
    debug.trace_fmtd(5, "=> local file: {f}; headers={{{h}}}",
                     f=local_filename, h=headers)

    debug.trace_fmtd(6, "download_web_document() => {d}", d=gh.elide(doc_data))
    return doc_data


def retrieve_web_document(url, meta_hash=None):
    """Simpler version of download_web_document, using an optional META_HASH for recording headers
    Note: works works around Error-403 presumably due to urllib's user agent"""
    # See https://stackoverflow.com/questions/34957748/http-error-403-forbidden-with-urlretrieve.
    debug.trace_fmtd(5, "retrieve_web_document({u})", u=url)
    result = None
    status_code = DEFAULT_STATUS_CODE
    if "//" not in url:
        url = "http://" + url
    try:
        r = requests.get(url)
        status_code = r.status_code
        result = r.content.decode(errors='ignore')
        if meta_hash is not None:
            meta_hash["headers"] = r.headers
    ## TODO: except(AttributeError, ConnectionError):
    except:
        system.print_exception_info("retrieve_web_document")
    debug.trace(5, f"status_code={status_code}")
    debug.trace_fmtd(7, "retrieve_web_document() => {r}", r=result)
    return result


def init_BeautifulSoup():
    """Make sure bs4.BeautifulSoup is loaded"""
    import bs4                           # pylint: disable=import-outside-toplevel, import-error
    global BeautifulSoup
    BeautifulSoup = bs4.BeautifulSoup
    return


def extract_html_link(html, url=None, base_url=None):
    """Returns list of all aref links in HTML. The optional URL and BASE_URL parameters can be specified to ensure the link is fully resolved."""
    debug.trace_fmtd(7, "extract_html_links(_):\n\thtml={h}", h=html)

    # Parse HTML, extract base URL if given and get website from URL.
    init_BeautifulSoup()
    soup = BeautifulSoup(html, 'html.parser')
    web_site_url = ""
    if url:
        web_site_url = re.sub(r"(https?://[^\/]+)/?.*", r"\1", url)
        debug.trace_fmtd(6, "wsu1={wsu}", wsu=web_site_url)
        if not web_site_url.endswith("/"):
            web_site_url += "/"
            debug.trace_fmtd(6, "wsu2={wsu}", wsu=web_site_url)
    # Determine base URL
    if base_url is None:
        base_url_info = soup.find("base")
        
        base_url = base_url_info.get("href") if base_url_info else None
        debug.trace_fmtd(6, "bu1={bu}", bu=base_url)
        if url and not base_url:
            # Remove parts of the URLafter the final slash
            base_url = re.sub(r"(^.*/[^\/]+/)[^\/]+$", r"\1", url)
            debug.trace_fmtd(6, "bu2={bu}", bu=base_url)
        if web_site_url and not base_url:
            base_url = web_site_url
            debug.trace_fmtd(6, "bu3={bu}", bu=base_url)
        if base_url and not base_url.endswith("/"):
            base_url += "/"
            debug.trace_fmtd(6, "bu4={bu}", bu=base_url)

    # Get links and resolve to full URL (TODO: see if utility for this)
    links = []
    all_links = soup.find_all('a')
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
        links.append(link_src)
    debug.trace_fmtd(6, "extract_html_links() => {i}", i=links)
    return links

#-------------------------------------------------------------------------------

def main(args):
    """Supporting code for command-line processing"""
    debug.trace_fmtd(6, "main({a})", a=args)
    user = system.getenv_text("USER")
    system.print_stderr("Warning, {u}: this is not really intended for direct invocation".format(u=user))

    # HACK: Do simple test of inner-HTML support
    # TODO: Do simpler test of download_web_document
    if (len(args) > 1):
        # Get web page text
        debug.trace_fmt(4, "browser_cache: {bc}", bc=browser_cache)
        url = args[1]
        debug.trace_expr(6, retrieve_web_document(url))
        html_data = download_web_document(url)
        filename = system.quote_url_text(url)
        if debug.debugging():
            write_temp_file("pre-" + filename, html_data)

        # Show inner/outer HTML
        # Note: The browser is hidden unless MOZ_HEADLESS true
        # TODO: Support Chrome
        ## OLD: wait_until_ready(url)
        ## BAD: rendered_html = render(html_data)
        system.setenv("MOZ_HEADLESS",
                      str(int(system.getenv_bool("MOZ_HEADLESS", True))))
        rendered_html = get_inner_html(url)
        if debug.debugging():
            write_temp_file("post-" + filename, rendered_html)
        print("Rendered html:")
        print(system.to_utf8(rendered_html))
        if debug.debugging():
            rendered_text = get_inner_text(url)
            debug.trace_fmt(5, "type(rendered_text): {t}", t=rendered_text)
            write_temp_file("post-" + filename + ".txt", rendered_text)
        debug.trace_fmt(4, "browser_cache: {bc}", bc=browser_cache)
    else:
        print("Specify a URL as argument 1 for a simple test of inner access")
    return

if __name__ == '__main__':
    main(sys.argv)
