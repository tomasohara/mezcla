#! /usr/bin/env python3
#
# Issues query via Bing Search API

# Notes:
# - The results can be cached to a local file to avoid using up search quota when
#   debugging with the same query. Multiple cached results are stored under temp dir.
# - Requires a Bing Search API key, which can be obtained via Windows Azure Marketplace:
#      https://azure.microsoft.com
# - Currently only 1000 queries per month are allowed without fee. (Previously it was 5k!)
# - Based originally on following tips:
#      https://stackoverflow.com/questions/27606478/search-bing-via-azure-api-using-python
# - Updgraded for Azure Cognitive Services:
#      https://docs.microsoft.com/en-us/azure/cognitive-services/bing-web-search/quickstarts/python
# - For the latest API as of Spring 2020, see
#      https://docs.microsoft.com/en-us/rest/api/cognitiveservices-bingsearch/bing-web-api-v7-reference
# - For operators that can be used, see
#      https://support.microsoft.com/en-us/topic/advanced-search-keywords-ea595928-5d63-4a0b-9c6b-0b769865e78a
# - New source for key and other info:
#      https://portal.azure.com/#view/Microsoft_Bing_Api
#      https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/quickstarts/rest/python
#
# TODO:
# - *** Have option to just show hit count. ***
# - Have option to just show results for misspelling (not Bing's replacement).
# - Have option to specify user agent.
# - Have option to download document for each result.
#

"""Issues queries via Bing Search API (using MS Azure Cognitive Services)"""

# Standard packages
## TEST: import base64
import json
import sys
from six.moves.urllib_parse import quote as quote_url       # pylint: disable=import-error
from six.moves.urllib.request import Request, build_opener  # pylint: disable=import-error
## OLD: import tempfile

# Local packages
## OLD: from mezcla import tpo_common as tpo
# TODO: import xml.dom.minidom
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system

BING_KEY = (system.getenv_value(
    "BING_KEY", None,
    desc="API key (via Microsoft Azure)") or "")
BING_BASE_URL = system.getenv_text(
    "BING_BASE_URL", "https://api.bing.microsoft.com/v7.0/",
    desc="URL for Bing API")
SEARCH = "search"
NEWS = "news/search"
IMAGES = "images"
VALID_SEARCH_TYPES = {SEARCH, IMAGES, "videos", NEWS}
DEFAULT_SEARCH_TYPE = SEARCH
SEARCH_TYPE = system.getenv_text(
    "SEARCH_TYPE", SEARCH,
    desc=f"Bing search type: {VALID_SEARCH_TYPES}"
)

## TODO3: track down TEMP_DIR not being set to gh.TEMP_BASE during test (subprocess issue?)
TEMP_FILE = gh.get_temp_file()
TEMP_DIR = gh.get_temp_dir()

USE_CACHE = system.getenv_bool(
    "USE_CACHE", False,
    desc="Use cached search results")

#...............................................................................

def bing_search(query, key=None, use_json=None, search_type=None, topn=None, non_phrasal=False):
    """Issue QUERY bing using API KEY returning result, optionally using JSON format by default or with alternative SEARCH_TYPE (e.g., image) or limited to TOPN results. The query is quoted unless NON_PHRASAL.
    Note: SEARCH_TYPE in {search, images, videos, news, SpellCheck}."""
    ## TODO: see if old search types RelatedSearch and Composite still supported
    debug.trace(4, f"bing_search{(query, key, use_json, search_type, topn)}")
    if search_type is None:
        search_type = SEARCH_TYPE
    if use_json is None:
        use_json = True
    debug.assertion(search_type in VALID_SEARCH_TYPES)
    if key is None:
        key = BING_KEY
    full_query = query if non_phrasal else ("'" + query + "'")
    query_spec = quote_url(full_query)

    # Create credential for authentication
    # TODO: make user_agent an option, along with ip_address
    user_agent = "Nonesuch/1.0 (python)"
    ## TEST:
    ## try:
    ##     colon_key_bytes = (":" + key).encode("utf-8")
    ##     encoded_colon_key = base64.b64encode(colon_key_bytes)
    ## except(TypeError, ValueError):
    ##     system.print_stderr("Exception in bing_search: {exc}", exc=sys.exc_info())
    ##     encoded_colon_key = ":???"
    ## auth = "Basic %s" % encoded_colon_key

    # Format search URL with optional format and top-n specification
    # TODO2: drop unused format_spec
    debug.assertion(use_json)
    format_spec = ""
    topn_spec = ("&count=%d" % topn) if topn else ""
    debug.trace_expr(5, format_spec, topn_spec)
    sources_spec = ""
    # HACK: if multiple types specified, comvert into Composite search
    if " " in search_type:
        sources = quote_url("'" + "+".join(search_type.split(" ")) + "'")
        sources = sources.replace("SpellingSuggestion", "spell").lower()
        sources_spec = "&Sources=" + sources
        search_type = "Composite"
    url_params = search_type + "?q=" + query_spec + sources_spec + topn_spec + format_spec
    url = BING_BASE_URL + "/" + url_params

    # Check cache if available
    response_data = None
    cache_file = system.form_path(TEMP_DIR, "_bs-" + url_params)
    if USE_CACHE and system.non_empty_file(cache_file):
        debug.trace_fmt(4, "Using cached results: {cf}", cf=cache_file)
        response_data = system.read_file(cache_file)
    
    # Download data from URL (unless cached).
    # Note: Also caches result
    if not response_data:
        debug.trace(3, f"Accessing URL {url!r}")
        request = Request(url)
        ## OLD: request.add_header("Authorization", auth)
        request.add_header("Ocp-Apim-Subscription-Key", key)
        request.add_header("User-Agent", user_agent)
        debug.trace(5, f"Headers: {request.header_items()!r}")
        request_opener = build_opener()
        response = request_opener.open(request) 
        response_data = response.read()
        if isinstance(response_data, bytes):
            debug.trace(4, "FYI: decoding binary response to text")
            response_data = response_data.decode("UTF-8", errors='ignore')
        if USE_CACHE:
            system.write_file(cache_file, response_data)

    # Format result
    debug.trace(5, f"Response: {response_data!r}")
    if use_json:
        json_result = json.loads(response_data)
        if debug.verbose_debugging():
            ## TODO: system.write_file(TEMP_FILE, str(json_result))
            ## TEST: hash_text = "\n".join([(str(k) + ": " + str(h)) for (k, h) in json_result.items()])
            ## system.write_file(TEMP_FILE, str(json_result))
            system.write_file(TEMP_FILE, system.to_string(response_data))
        ## TODO: result_list = json_result["webPages"]["value"]
        result_list = json_result
    else:
        result_list = response_data
        ## TODO: xml_result = xml.dom.minidom.parseString(response_data)
        ## TODO: result_list = xml_result.toprettyxml()
    ## TODO2:" result_list => result_hash
    debug.trace_expr(5, result_list, max_len=4096)
    return result_list

#...............................................................................

def main():
    """Entry point for script"""
    search_type = SEARCH
    use_json = True
    
    # Check command-line arguments (TODO: convert to main.py)
    i = 1
    show_usage = (i >= len(sys.argv))
    while (i < len(sys.argv) and (sys.argv[i][0] == "-")):
        if (sys.argv[i] == "--json"):
            use_json = True
        elif (sys.argv[i] == "--xml"):
            use_json = False
        elif (sys.argv[i] == "--image"):
            search_type = IMAGES
        elif (sys.argv[i] == "--type"):
            i += 1
            search_type = sys.argv[i]
        else:
            show_usage = True
        i += 1
    if (show_usage):
        print("Usage: %s [--json | --xml] [--image] [--type label] query_word ..." % sys.argv[0])
        print("")
        print("Example:")
        print("    {script} ScrappyCito -dog".format(script=gh.basename(__file__)))
        print("")
        print("Notes:")
        print("- Set BING_KEY to key obtained via Microsoft Azure; see following:")
        print("  https://learn.microsoft.com/en-us/azure/cognitive-services/bing-web-search")
        print("- Types: Web, Image, Video, News, SpellingSuggestion, RelatedSearch")
        print("- For API details, see following:")
        print("  https://docs.microsoft.com/en-us/rest/api/cognitiveservices-bingsearch/bing-web-api-v7-reference")
        print("- The result is XML file with <entry> tags for blurb info")
        print("- ** XML support is currently broken.")
        sys.exit()
    debug.assertion(BING_KEY)

    # Issue query and print result
    query = " ".join(sys.argv[i:])
    print(bing_search(query, use_json=use_json, search_type=search_type))
    return


if __name__ == "__main__":
    main()
