#! /usr/bin/env python3
#
# Test(s) for ../html_utils.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_html_utils.py
# - Global pylint filter:
#   pylint: disable=protected-access
#   -- TEMP: filter (TODO2: make sure just test_xyz)
#       pylint: disable=missing-function-docstring
#
# TODO2:
# - Fix the type hints tests, which need special support using Pydantic (or mypy):
#   see test_fix_url_parameters_type_hints.
# - Use website accessible to all ScrappyCito assistants. For example,
#      www.tomasohara.trade => new www.scrappycito.trade
#   

"""Tests for html_utils module"""

# Standard packages
import os

# Installed packages
from PIL import Image
import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import debug
from mezcla import misc_utils
from mezcla import system
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla.tests.common_module import normalize_text

# Note: Two references are used for the module to be tested:
#    THE_MODULE:            global module object
import mezcla.html_utils as THE_MODULE

# Constants and environment options
TEST_SELENIUM_DESC = "Include tests requiring selenium"
TEST_SELENIUM = system.getenv_bool(
    "TEST_SELENIUM", False,
    desc=TEST_SELENIUM_DESC)
SKIP_SELENIUM = not TEST_SELENIUM
SKIP_SELENIUM_REASON = f"Not-{TEST_SELENIUM_DESC}"
#
INCLUDE_HINT_TESTS = system.getenv_bool(
    "INCLUDE_HINT_TESTS", False,
    desc="Include the work-in-progress tests involving type hints")
SKIP_HINT_TESTS = not INCLUDE_HINT_TESTS
SKIP_HINT_REASON = "Type hinting tests require more work"
##
SCRAPPYCITO_URL = "http://www.scrappycito.com"
TOMASOHARA_TRADE_URL = "http://www.tomasohara.trade"
SCRAPPYCITO_LIKE_URL = system.getenv_text(
    "SCRAPPYCITO_LIKE_URL", f"{TOMASOHARA_TRADE_URL}:9330",
    desc=f"URL to use instead of {SCRAPPYCITO_URL}")
TOMASOHARA_TRADE_LIKE_URL = system.getenv_text(
    "TOMASOHARA_TRADE_LIKE_URL", TOMASOHARA_TRADE_URL,
    desc=f"URL to use instead of {TOMASOHARA_TRADE_URL} like localhost://tomasohara")
PACMAN_FILENAME = gh.form_path("examples", "sd-spooky-pacman.png")
##
DIMENSIONS_HTML_FILENAME = gh.form_path("resources", "simple-window-dimensions.html")
DIMENSIONS_EXPECTED_TEXT = """
   Simple window dimensions

   Simple window dimensions

      Legend:
        Screen dimensions:    ???
        Browser dimensions:   ???

   JavaScript is required
"""
#
# NOTE: Whitespace and punctuation gets normalized
# TODO: restore bullet points (e.g., "* Screen dimensions")

# Global initialization
## TODO3: Do via class setup method(s), monkey patching, and/or download-dir arg
## (e.g., download_dir for download_web_document).
## TODO4: Also, extend get_temp_dir to use TEMP_BASE automatically.
THE_MODULE.DOWNLOAD_DIR = gh.form_path(gh.get_temp_dir(use_temp_base=True),
                                       "downloads", create=True)

#-------------------------------------------------------------------------------

def resolve_mezcla_path(filename):
    """Determine path for FILENAME using heurtics based on repo layout"""
    # example: resolve_mezcla_path("examples/sd-spooky-pacman.png") => "/home/tomohara/Mezcla/mezcla/examples/sd-spooky-pacman.png"
    result = gh.resolve_path(filename, heuristic=True, absolute=True)
    debug.trace(6, f"resolve_mezcla_path({filename!r}) => {result!r}")
    return result

def resolve_mezcla_url(filename):
    """Determine URL for mezcla FILENAME in repo"""
    # example: resolve_mezcla_url("examples/sd-spooky-pacman.png") => "https://github.com/tomasohara/mezcla/blob/main/mezcla/examples/sd-spooky-pacman.png"
    ## TEST: url = f"https://github.com/tomasohara/mezcla/blob/main/mezcla/{filename}"
    url = f"{TOMASOHARA_TRADE_LIKE_URL}/mezcla/mezcla/{filename}"
    ## TODO?: url = f"http://localhost/mezcla/mezcla/{filename}"
    debug.trace(6, f"resolve_mezcla_url({filename!r}) => {url!r}")
    return url

#-------------------------------------------------------------------------------

class TestHtmlUtils(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    use_temp_base_dir = True
    ##
    ## NOTE: Using personal site instead of LLC in order to avoid issues
    ## with the production server (i.e., www.scrappycito.com).
    scrappycito_url = "www.scrappycito.com"
    scrappycito_like_url = SCRAPPYCITO_LIKE_URL
    tomasohara_trade_url = TOMASOHARA_TRADE_URL
    tomasohara_trade_like_url = TOMASOHARA_TRADE_LIKE_URL
    ready_test_path = resolve_mezcla_path("document_ready_test.html")
    ready_test_alt_path = resolve_mezcla_path("document_ready_test_alt.html")
    dimensions_url = "file://" + resolve_mezcla_path(DIMENSIONS_HTML_FILENAME)
    pacman_path = resolve_mezcla_path(PACMAN_FILENAME)
    pacman_url = resolve_mezcla_url(PACMAN_FILENAME)

    @pytest.mark.skipif(SKIP_SELENIUM, reason=SKIP_SELENIUM_REASON)
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_browser(self):
        """Verify get_browser() returns object with HTML"""
        debug.trace(4, "test_get_browser()")
        browser = THE_MODULE.get_browser(self.tomasohara_trade_url)
        self.do_assert(my_re.search(r"<title>.*Tomás.*O.Hara.*Scrappy.*Cito.*</title>",
                                    browser.page_source))
        THE_MODULE.shutdown_browser(browser)

    def test_get_url_parameter_value(self):
        """Ensure get_url_parameter_value works as expected"""
        debug.trace(4, "test_get_url_parameter_value()")
        save_user_parameters = THE_MODULE.user_parameters
        THE_MODULE.user_parameters = {}
        assert THE_MODULE.get_url_parameter_value("fu-bar", None) is None
        assert THE_MODULE.get_url_parameter_value("fu-bar", None, {"fu-bar": "fu"}) == "fu"
        THE_MODULE.user_parameters = {"fu-bar": "bar"}
        assert THE_MODULE.get_url_parameter_value("fu-bar", None) == "bar"
        assert THE_MODULE.get_url_parameter_value("fu_bar", None) == "bar"
        assert THE_MODULE.get_url_parameter_value("fu-bar", None, {"fu-bar": "fu"}) == "fu"
        THE_MODULE.user_parameters = save_user_parameters
        return

    @pytest.mark.skipif(SKIP_SELENIUM, reason=SKIP_SELENIUM_REASON)
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_inner_text(self):
        """Verify that JavaScript fills in window dimensions
        Note: requires selenium"""
        debug.trace(4, "test_get_inner_text()")
        html_filename = "simple-window-dimensions.html"
        html_path = resolve_mezcla_path(html_filename)
        url = ("file:" + system.absolute_path(html_path))
        # TODO: use direct API call to return unrendered text
        unrendered_text = gh.run(f"lynx -dump {url}")
        debug.trace_expr(5, unrendered_text)
        assert my_re.search(r"Browser dimensions: \?", unrendered_text)
        rendered_text = THE_MODULE.get_inner_text(url)
        debug.trace_expr(5, rendered_text)
        assert my_re.search(r"Browser dimensions: \d+x\d+", rendered_text)

    @pytest.mark.skipif(SKIP_SELENIUM, reason=SKIP_SELENIUM_REASON)
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_inner_html(self):
        """Verify that JavaScript fills in window dimensions
        Note: requires selenium"""
        debug.trace(4, "test_get_inner_html()")
        html_filename = "simple-window-dimensions.html"
        html_path = resolve_mezcla_path(html_filename)
        url = ("file:" + system.absolute_path(html_path))
        # TODO: use direct API call to return unrendered text
        unrendered_html = gh.run(f"lynx -source {url}")
        debug.trace_expr(5, unrendered_html)
        assert my_re.search(
            r"<li>Browser dimensions:\s*<span.*>\?\?\?</span></li>",
            unrendered_html,
            )
        rendered_html = THE_MODULE.get_inner_html(url)
        debug.trace_expr(5, rendered_html)
        assert my_re.search(
            r"<li>Browser dimensions:\s*<span.*>\d+x\d+</span></li>",
            rendered_html,
            )

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_scrappycito_urls(self):
        """Some sanity checks on URLs for ScrappyCito, LLC and Tom O'Hara's consulting.
        Note: www.scrappycito.com should be avoided and www.tomasohara.trade used instead.
        """
        debug.trace(4, f"TestIt.test_scrappycito_urls(); self={self}")
        self.do_assert("scrappycito.com" in self.scrappycito_url)
        self.do_assert("scrappycito.com" not in self.scrappycito_like_url,
                       f"The production server should not be used in tests: {self.scrappycito_url}")        
        self.do_assert("tomasohara" in self.scrappycito_like_url)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_main_url_content(self):
        """Make sure expected web content at scrappycito-like and tomasohara.trade[-like] URLs"""
        debug.trace(4, f"TestIt.test_main_url_content(); self={self}")
        content = THE_MODULE.download_web_document(self.scrappycito_like_url)
        assert "Welcome to ScrappyCito" in content
        content = THE_MODULE.download_web_document(self.tomasohara_trade_url)
        assert "Little Scrap" in content
        
    def check_inner_html(self, regular, inner):
        """Helper for inner html tests: makes sure that Javascript generated output not in REGULAR but is in INNER output for ScrappyCito's landing page
        Note: This assumes inner produced with ?section=tips option.
        """
        # note: the triangle points south (v) when the section is open, as assumed for inner:
        #       <span id="ui-tips-id" class="ui-icon ui-icon-triangle-1-e"></span>   [closed (east):  >]
        #   vs. <span id="ui-tips-id" class="ui-icon ui-icon-triangle-1-s"></span>   [opened (south): v]
        # TODO3: use HTML file in repo
        debug.trace_expr(5, self, regular, inner,
                         prefix="TestIt.check_inner_html: ", max_len=128)
        tips_section_open_regex = r"tips-id.*ui-icon-triangle-1-s"
        self.do_assert(my_re.search(tips_section_open_regex, inner.strip(), flags=my_re.IGNORECASE))
        self.do_assert(not my_re.search(tips_section_open_regex, regular.strip(), flags=my_re.IGNORECASE))
        tips_section_closed_regex = r"tips-id.*ui-icon-triangle-1-e"
        self.do_assert(not my_re.search(tips_section_closed_regex, inner.strip(), flags=my_re.IGNORECASE))
        self.do_assert(my_re.search(tips_section_closed_regex, regular.strip(), flags=my_re.IGNORECASE))
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_inner_html_alt(self):
        """Alternative test of get_inner_html"""
        debug.trace(4, f"TestIt.test_get_inner_html_alt(); self={self}")
        debug.assertion("scrappycito.com" not in self.scrappycito_like_url,
                        f"The production server should not be used in tests: {self.scrappycito_url}")
        ## TODO: regular_output = THE_MODULE.download_web_document(self.scrappycito_like_url)
        regular_output = gh.run(f"lynx -source {self.scrappycito_like_url}")
        inner_output = THE_MODULE.get_inner_html(self.scrappycito_like_url + "/?section=tips")
        self.check_inner_html(regular_output, inner_output)
        return

    @pytest.mark.skipif(SKIP_SELENIUM, reason=SKIP_SELENIUM_REASON)
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_run_script_for_inner_html(self):
        """Test of getting inner HTML via script invocation"""
        debug.trace(4, f"TestIt.test_run_script_for_inner_html(); self={self}")
        regular_output = self.run_script(options=f"--stdout {self.scrappycito_like_url}")
        self.temp_file += "-2"
        inner_output = self.run_script(options=f"--inner --stdout {self.scrappycito_like_url + '/?section=tips'}")
        self.check_inner_html(regular_output, inner_output)
        return

    @pytest.mark.skipif(SKIP_SELENIUM, reason=SKIP_SELENIUM_REASON)
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_document_ready(self):
        """Ensure document_ready() works as expected"""
        debug.trace(4, "test_document_ready()")
        google_search_ready = THE_MODULE.document_ready("https://www.google.com")
        self.do_assert(google_search_ready)
        ## TEST:
        ## twitter_x_feed_ready = THE_MODULE.document_ready("https://x.com/X")
        ## self.do_assert(not twitter_x_feed_ready)
        debug.assertion("15 seconds" in system.read_file(self.ready_test_path))
        test_document_ready = THE_MODULE.document_ready("file://" + self.ready_test_path, timeout=5)
        self.do_assert(not test_document_ready)

    def test_escape_html_value(self):
        """Ensure escape_html_value() works as expected"""
        debug.trace(4, "test_escape_html_value()")
        assert THE_MODULE.escape_html_value("<2/") == "&lt;2/"
        assert THE_MODULE.escape_html_value("Joe's hat") == "Joe&#x27;s hat"

    def test_unescape_html_value(self):
        """Ensure unescape_html_value() works as expected"""
        debug.trace(4, "test_unescape_html_value()")
        assert THE_MODULE.unescape_html_value("&lt;2/") == "<2/"
        assert THE_MODULE.unescape_html_value("Joe&#x27;s hat") == "Joe's hat"

    def test_escape_hash_value(self):
        """Ensure escape_hash_value() works as expected"""
        debug.trace(4, "test_escape_hash_value()")
        hash_table = {
            'content-type': 'multipart/form-data;\n',
            'name': 'description'
        }
        assert THE_MODULE.escape_hash_value(hash_table, 'content-type') == 'multipart/form-data;<br>'

    def test_get_param_dict(self):
        """Ensure get_param_dict() works as expected"""
        debug.trace(4, "test_get_param_dict()")
        THE_MODULE.user_parameters = {
            'https-port': '443',
            'not-found-status': '404',
            'redirect-status': '302'
        }
        assert THE_MODULE.get_param_dict().get('not-found-status') == '404'
        assert THE_MODULE.get_param_dict() == THE_MODULE.user_parameters

    def test_set_param_dict(self):
        """Ensure set_param_dict() works as expected"""
        debug.trace(4, "test_set_param_dict()")
        THE_MODULE.user_parameters = {
            'not-found-status': '404',
            'redirect-status': '302'
        }
        new_user_parameters = {'https-port': '443'}
        THE_MODULE.issued_param_dict_warning = False
        THE_MODULE.set_param_dict(new_user_parameters)
        assert THE_MODULE.user_parameters == new_user_parameters
        assert THE_MODULE.issued_param_dict_warning

    def test_get_url_param(self):
        """Ensure get_url_param() works as expected"""
        debug.trace(4, "test_get_url_param()")
        THE_MODULE.user_parameters = {
            'not-found-status': '404',
            'redirect-status': '302',
            'default-body': "Joe's hat"
        }
        assert THE_MODULE.get_url_param('redirect-status') == '302'
        assert THE_MODULE.get_url_param('redirect_status') == '302'
        assert THE_MODULE.get_url_param('bad-request-status', default_value='400') == '400'
        assert THE_MODULE.get_url_param('default-body', escaped=True) == 'Joe&#x27;s hat'

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_url_param_checkbox_spec(self):
        """Ensure get_url_param_checkbox_spec() works as expected"""
        debug.trace(4, "test_get_url_param_checkbox_spec()")
        param_dict = {"check_1_on": "on",  "check_3_on": "True",  "check_5_on": 1,
                      "check_2_off": "off", "check_4_off": False, "check_6_off": None}

        # Test multiple positive cases
        assert THE_MODULE.get_url_param_checkbox_spec("check_1_on", param_dict=param_dict)
        assert THE_MODULE.get_url_param_checkbox_spec("check_3_on", param_dict=param_dict)
        assert THE_MODULE.get_url_param_checkbox_spec("check_5_on", param_dict=param_dict)

        # test non-checked and non-existent check cases
        assert not THE_MODULE.get_url_param_checkbox_spec("check_2_off", param_dict=param_dict)
        assert not THE_MODULE.get_url_param_checkbox_spec("check_4_off", param_dict=param_dict)
        assert not THE_MODULE.get_url_param_checkbox_spec("check_6_off", param_dict=param_dict)
        assert not THE_MODULE.get_url_param_checkbox_spec("check_7_missing", param_dict=param_dict)

    def test_get_url_parameter_bool(self):
        """Ensure get_url_parameter_bool() works as expected"""
        debug.trace(4, "test_get_url_parameter_bool()")
        assert THE_MODULE.get_url_parameter_bool("abc", False, { "abc": "on" })
        assert THE_MODULE.get_url_param_bool("abc", False, { "abc": "True" })

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_url_parameter_int(self):
        """Ensure get_url_parameter_int() works as expected"""
        debug.trace(4, "test_get_url_parameter_int()")
        assert THE_MODULE.get_url_parameter_int("abc", 0, { "abc": "123" }) == 123
        assert THE_MODULE.get_url_parameter_int("abc", 0, { "abc": "123.4" }) == 0
        assert THE_MODULE.get_url_parameter_int("abc", 0, { "abc": "not int" }) == 0

    def test_fix_url_parameters(self):
        """Ensure fix_url_parameters() works as expected"""
        debug.trace(4, "test_fix_url_parameters()")
        assert THE_MODULE.fix_url_parameters({'w_v':[7, 8], 'h_v':10}) == {'w-v':8, 'h-v':10}

    def test_expand_misc_param(self):
        """Ensure expand_misc_param() works as expected"""
        debug.trace(4, "test_expand_misc_param()")
        misc_dict = {
            'x': 1,
            'y': 2,
            'z': 'a=3, b=4',
        }
        expected = {
            'x': 1,
            'y': 2,
            'z': 'a=3, b=4',
            'a': '3',
            'b': '4',
        }
        assert THE_MODULE.expand_misc_param(misc_dict, 'z') == expected

    @pytest.mark.xfail                   # TODO: remove xfail
    def test__read_file(self):
        """Ensure _read_file() works as expected"""
        debug.trace(4, "test__read_file()")

        # test valid file
        temp_file = self.get_temp_file()
        system.write_file(temp_file, 'file\nwith\nmultiple\nlines\n')
        assert (
            THE_MODULE._read_file(filename=temp_file, as_binary=False) ==
            'file\nwith\nmultiple\nlines\n')

        # Test invalid file
        self.patch_trace_level(3)
        THE_MODULE._read_file(filename='invalid_file', as_binary=False)
        captured = self.get_stderr()
        assert "Unable to read file" in captured

        # Test binary mode
        test_filename = self.create_temp_file("open binary")
        assert (
            THE_MODULE._read_file(filename=test_filename, as_binary=True) ==
            bytes("open binary"+ os.linesep , "UTF-8"))

    @pytest.mark.xfail                   # TODO: remove xfail
    def test__write_file(self):
        """Ensure _write_file() works as expected"""
        debug.trace(4, "test__write_file()")
        # Test normal usage
        filename = self.get_temp_file()
        THE_MODULE._write_file(filename, "it", as_binary=False)
        assert THE_MODULE._read_file(filename=filename, as_binary=False) == "it\n"

        # Test binary mode
        filename = self.get_temp_file()
        THE_MODULE._write_file(filename, data=bytes("it", encoding="UTF-8"), as_binary=True)
        assert THE_MODULE._read_file(filename=filename, as_binary=True) == b"it"

    def check_download_web_document(self, download_func):
        """Check web downloads via DOWNLOAD_FUNC"""
        ## TODO2: change to html file from repo
        assert "currency" in THE_MODULE.download_web_document(f"{self.tomasohara_trade_like_url}/Dollar_-_Simple_English_Wikipedia_the_free_encyclopedia.html")
        assert download_func("www. bogus. url.html") is None
        remote_pacman_image_data = download_func(self.pacman_url, as_binary=True)
        local_pacman_image_data = system.read_binary_file(self.pacman_path)
        assert len(remote_pacman_image_data) == len(local_pacman_image_data)
        assert remote_pacman_image_data == local_pacman_image_data

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_old_download_web_document(self):
        """Ensure old_download_web_document() works as expected"""
        self.check_download_web_document(download_func=THE_MODULE.old_download_web_document)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_download_web_document(self):
        """Ensure download_web_document() works as expected"""
        debug.trace(4, "test_download_web_document()")
        ## NOTE: Wikipedia/WikiMedia complaining about robots (even though single document access)
        ## during GitHub actions run. See https://wikitech.wikimedia.org/wiki/Robot_policy.
        ## TODO2: use website accessible to all team members
        self.check_download_web_document(download_func=THE_MODULE.download_web_document)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_test_download_html_document(self):
        """Ensure test_download_html_document() works as expected"""
        debug.trace(4, "test_test_download_html_document()")
        assert "Google" in THE_MODULE.test_download_html_document("www.google.com")
        ## TODO2: use website accessible to all team members
        assert "Tomás" not in THE_MODULE.test_download_html_document(f"{self.tomasohara_trade_like_url}", encoding="big5")

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_download_html_document(self):
        """Ensure download_html_document() works as expected"""
        debug.trace(4, "test_download_html_document()")

        # Set tmp_dir and filename for testing
        tmp_dir = system.getenv("TMP")
        filename = "test_download_file"

        # Assert file is downloaded and created in tmp_dir
        THE_MODULE.download_html_document(self.tomasohara_trade_like_url, download_dir=tmp_dir, filename=filename)
        assert filename in system.read_directory(tmp_dir)

        # Assert exception report is printed when not Ignore
        try :
            _ = THE_MODULE.download_html_document("", ignore=False)
        except:
            pass
        err = self.get_stderr()
        assert "Error during retrieve_web_document" in err

        # Assert exception report is not printed when Ignore
        self.clear_stderr()
        try :
            _ = THE_MODULE.download_html_document("", ignore=True)
        except:
            pass
        err = self.get_stderr()
        assert "Error during retrieve_web_document" not in err

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_download_binary_file(self):
        """Ensure download_binary_file() works as expected"""
        debug.trace(4, "test_download_binary_file()")
        binary_doc = THE_MODULE.download_binary_file(url=self.tomasohara_trade_like_url)
        non_binary_doc = THE_MODULE.download_web_document(url=self.tomasohara_trade_like_url)
        assert my_re.search(b"Scrappy.*Cito", binary_doc)
        assert bytes(non_binary_doc, encoding="UTF-8") == binary_doc


    def test_retrieve_web_document(self):
        """Ensure retrieve_web_document() works as expected"""
        debug.trace(4, "test_retrieve_web_document()")
        assert my_re.search("Scrappy.*Cito", THE_MODULE.retrieve_web_document(self.tomasohara_trade_like_url))

    def test_init_BeautifulSoup(self):
        """Ensure init_BeautifulSoup() works as expected"""
        debug.trace(4, "test_init_BeautifulSoup()")
        THE_MODULE.BeautifulSoup = None
        THE_MODULE.init_BeautifulSoup()
        assert THE_MODULE.BeautifulSoup
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_extract_html_link(self):
        """Ensure extract_html_link() works as expected"""
        debug.trace(4, "test_extract_html_link()")

        url = "https://www.example.com"
        html = (
            '<!DOCTYPE html>\n'
            '<html>\n'
            '<body>\n'
            '<h2>The target Attribute</h2>\n'
            '<div class="some-class">this is a div</div>\n'
            '<div class="some-class another-class">'
            '<a href="https://www.anothersite.io/" target="_blank">another site</a>\n'
            '<a href="https://www.example.com/" target="_blank">Visit Example!</a>\n'
            '<a href="https://www.example.com/sopport" target="_blank">example sopport</a>\n'
            '</div>'
            '<a href="https://www.subdomain.example.com/" target="_blank">Visit subdomain of Example!</a>\n'
            '<a href="https://www.example.com.br/" target="_blank">visit Example Brazil!</a>\n'
            '<p>If target="_blank", this is a link.</p>\n'
            '<a href="www.subdomain.example.com/sitemap.xml" target="_blank">see the sitemap</a>\n'
            '<a href="/home.html" target="_blank">home page</a>\n'
            '</body>\n'
            '</html>\n'
        )
        all_urls = [
            'https://www.anothersite.io/',
            'https://www.example.com/',
            'https://www.example.com/sopport',
            'https://www.subdomain.example.com/',
            'https://www.example.com.br/',
            'https://www.example.com/www.subdomain.example.com/sitemap.xml',
            'https://www.example.com/home.html',
        ]

        # Test extract all urls from html
        assert THE_MODULE.extract_html_link(html, url=url, base_url=url) == all_urls

        # Test base_url none
        assert THE_MODULE.extract_html_link(html, url=url) == all_urls

    @pytest.mark.xfail
    @pytest.mark.skipif(SKIP_HINT_TESTS, reason=SKIP_HINT_REASON)
    def test_get_inner_html_type_hints(self):
        URL_VALID = "https://duckduckgo.com"
        URL_INVALID = "duckduckgo.com"
        assert THE_MODULE.get_inner_html(URL_VALID)
        assert not THE_MODULE.get_inner_html(URL_INVALID)

    @pytest.mark.xfail
    def test_get_inner_text_alt(self):
        URL_VALID = "https://duckduckgo.com"
        URL_INVALID = "duckduckgo.com"
        inner_text_valid = THE_MODULE.get_inner_text(URL_VALID)
        inner_text_invalid = THE_MODULE.get_inner_text(URL_INVALID)
        keywords = ["DuckDuckGo", "private", "free", "browser", "search", "ads"]
        assert all(word in inner_text_valid for word in keywords)
        assert not inner_text_invalid

    @pytest.mark.skipif(SKIP_SELENIUM, reason=SKIP_SELENIUM_REASON)
    @pytest.mark.xfail
    def test_document_ready_alt(self):
        """Verify document_ready for simple sites"""
        ## TODO2: merge with test_document_ready; use simple site (not production web search)
        URL_VALID = "https://duckduckgo.com"
        assert (THE_MODULE.document_ready(URL_VALID))
        
        ## Note: following should not be ready at first due to JavaScript (n.b., wrong assumption).
        ## TODO3: use different URL because the JavaScript doesn't affect ready status; see test_document_ready
        scrappycito_search_result = f"{self.scrappycito_like_url}/run_search?query=modern+art"
        assert THE_MODULE.document_ready(scrappycito_search_result)

        # Use example suggesed by Claude-Opus-4.1
        debug.assertion("15 seconds" in system.read_file(self.ready_test_alt_path))
        test_document_ready = THE_MODULE.document_ready("file://" + self.ready_test_alt_path, timeout=5)
        self.do_assert(not test_document_ready)

    def check_browser_dimensions(self, width, height, label):
        """Verify that browser accepts dimensions of WIDTH x HEIGHT via selenium"""
        debug.trace(5, f"check_browser_dimensions{(width, height, label)}")
        # Note: The cache is disabled, so browser object for URL has right options.
        self.monkeypatch.setattr(THE_MODULE, "USE_BROWSER_CACHE", False)
        self.monkeypatch.setattr(THE_MODULE, "BROWSER_DIMENSIONS", f"{width},{height}")
        browser = THE_MODULE.get_browser(self.dimensions_url)
        screenshot_path = gh.form_path(self.get_temp_dir(), f"{label}-screenshot.png")
        try:
            browser.get_screenshot_as_file(screenshot_path)
            ok = True
            with Image.open(screenshot_path) as img:
                actual_width, actual_height = img.size
                debug.trace_expr(5, actual_width, actual_height)
        except:
            ok = False
            debug.trace_exception_info(6, "get_screenshot_as_file")
        ok = ok and misc_utils.is_close(width, actual_width, epsilon=1000)
        ok = ok and misc_utils.is_close(height, actual_height, epsilon=1000)
        THE_MODULE.shutdown_browser(browser)
        return ok
        
    @pytest.mark.skipif(SKIP_SELENIUM, reason=SKIP_SELENIUM_REASON)
    @pytest.mark.xfail
    def test_browser_dimensions(self):
        """Verify that 8k and 16k resolution possible with headless selenium driver but not 32k"""
        # In addition, the target 16k resolution is based on
        #    https://en.wikipedia.org/wiki/16K_resolution
        # It is comparable to four 4k monitors. Also see
        #    https://en.wikipedia.org/wiki/Display_resolution_standards
        debug.trace(4, "test_browser_dimensions()")
        assert self.check_browser_dimensions(3840, 2160, "4k")
        assert self.check_browser_dimensions(7680, 4320, "8k")
        assert self.check_browser_dimensions(15360, 8640, "16k")
        assert not self.check_browser_dimensions(30720, 17280, "32k")

    @pytest.mark.skipif(SKIP_SELENIUM, reason=SKIP_SELENIUM_REASON)
    @pytest.mark.xfail
    def test_wait_until_ready(self):
        """Verify that wait_until_ready for simple web page with JavaScript"""
        debug.trace(4, "test_wait_until_ready()")
        self.patch_trace_level(5)
        THE_MODULE.wait_until_ready(self.dimensions_url)
        captured = self.get_stderr()
        # ex: Stable size check: last=-1 size=1140 diff=1140 count=0 done=False
        assert my_re.search(r"diff=[0-9]", captured)

    @pytest.mark.skipif(SKIP_SELENIUM, reason=SKIP_SELENIUM_REASON)
    @pytest.mark.xfail
    def test_browser_command(self):
        """Verify that browser_command works for simple command"""
        debug.trace(4, "test_browser_command()")
        title = THE_MODULE.browser_command(url=self.dimensions_url,
                                           command="return document.title;")
        # ex: "Simple window dimensions"
        assert "dimensions" in title.lower()

    @pytest.mark.skipif(SKIP_SELENIUM, reason=SKIP_SELENIUM_REASON)
    @pytest.mark.xfail
    def test_selenium_function(self):
        """Verify that selenium_function works for simple function call"""
        debug.trace(4, "test_selenium_function()")
        result = THE_MODULE.selenium_function(url=self.dimensions_url,
                                              call="set_window_rect(width=123, height=123)")
        # ex: {'x': 0, 'y': 0, 'width': 450, 'height': 123}
        assert my_re.search(r"'width': \d+, 'height': \d+", result)

    @pytest.mark.xfail
    def test_set_param_dict_alt(self):
        param_dict = {
            1: "a+b+c",
            2: "a%2b%2c%2"
        }
        THE_MODULE.set_param_dict(param_dict)
        assert THE_MODULE.user_parameters == param_dict

    @pytest.mark.xfail
    @pytest.mark.skipif(SKIP_HINT_TESTS, reason=SKIP_HINT_REASON)
    def test_set_param_dict_type_hints(self):
        param_dict = str({1: "a+b+c", 2: "a%2b%2c%2"})
        THE_MODULE.set_param_dict(param_dict)
        assert not isinstance(THE_MODULE.user_parameters, dict)
        assert len(THE_MODULE.user_parameters) > 2

    @pytest.mark.xfail    
    @pytest.mark.skipif(SKIP_HINT_TESTS, reason=SKIP_HINT_REASON)
    def test_get_param_dict_type_hints(self):
        param_dict = str({
            "p1": "a+b+c",
            "p2": "a%2b%2c%2"
        })
        result = THE_MODULE.get_param_dict(param_dict=param_dict)
        assert not isinstance(result, dict)

    @pytest.mark.xfail 
    @pytest.mark.skipif(SKIP_HINT_TESTS, reason=SKIP_HINT_REASON)
    def test_get_url_param_type_hints(self):
        param_dict = {
            "name": "Terry",
            "age": "30"
        }
        name = "name"
        default_value = "Default"
        escaped = False
        result = THE_MODULE.get_url_param(name, default_value, param_dict, escaped)

        assert isinstance(name, str)
        assert isinstance(default_value, str) or default_value is None
        assert isinstance(param_dict, dict) or param_dict is None
        assert isinstance(escaped, bool)
        assert isinstance(result, str)
    
    @pytest.mark.xfail 
    @pytest.mark.skipif(SKIP_HINT_TESTS, reason=SKIP_HINT_REASON)
    def test_get_url_text_type_hints(self):
        param_dict = {
            "name": "Alice",
            "age": 28,
            "city": "New York",
            "is_student": False,
            "grades": [85, 90, 78, 92, 88]
        }

        name = "name"
        default_value = "default"
        
        result = THE_MODULE.get_url_text(name, default_value, param_dict)
        assert isinstance(result, str)
        assert isinstance(name, str)
        assert isinstance(default_value, str) or default_value is None
        assert isinstance(param_dict, dict) or param_dict is None

        result = THE_MODULE.get_url_text(None)
        assert isinstance(result, str)

    @pytest.mark.xfail 
    @pytest.mark.skipif(SKIP_HINT_TESTS, reason=SKIP_HINT_REASON)
    def test_get_url_param_checkbox_spec_type_hints(self):
        name = "param"
        default_value = ""
        param_dict = {name: "on"}

        result = THE_MODULE.get_url_param_checkbox_spec(name, default_value, param_dict)

        assert isinstance(name, str)
        assert isinstance(default_value, (bool, str)) or default_value is None
        assert isinstance(param_dict, dict) or param_dict is None
        assert isinstance(result, str)  # Result should always be a string

        result = THE_MODULE.get_url_param_checkbox_spec(None)
        assert isinstance(result, str)

    @pytest.mark.xfail 
    @pytest.mark.skipif(SKIP_HINT_TESTS, reason=SKIP_HINT_REASON)
    def test_get_url_parameter_value_type_hints(self):
        param = "param"
        default_value = ""
        param_dict = {param: ["on", "off", "neutral"]}
        
        result = THE_MODULE.get_url_parameter_value(param, default_value, param_dict)

        assert isinstance(param, str)
        assert isinstance(default_value, (str, type(None)))  # Union of Any and None
        assert isinstance(param_dict, dict) or param_dict is None
        assert isinstance(result, (str, str))  # Union of string and Any type

        result = THE_MODULE.get_url_parameter_value(None)
        assert result is None

    @pytest.mark.xfail 
    @pytest.mark.skipif(SKIP_HINT_TESTS, reason=SKIP_HINT_REASON)
    def test_get_url_parameter_bool_type_hints(self):
        param = "param"
        default_value = False
        param_dict = {param: "on"}
        
        result = THE_MODULE.get_url_parameter_bool(param, default_value, param_dict)

        assert isinstance(param, str)
        assert isinstance(default_value, bool)
        assert isinstance(param_dict, dict) or param_dict is None
        assert not isinstance(result, str)
        assert isinstance(result, bool)

        result = THE_MODULE.get_url_parameter_bool(None)
        assert isinstance(result, bool)

    @pytest.mark.xfail 
    @pytest.mark.skipif(SKIP_HINT_TESTS, reason=SKIP_HINT_REASON)
    def test_get_url_parameter_int_type_hints(self):
        param = "param"
        default_value = 0
        param_dict = {param: 9}

        result = THE_MODULE.get_url_parameter_int(param, default_value, param_dict)

        assert isinstance(param, str)
        assert isinstance(default_value, int)
        assert isinstance(param_dict, dict) or param_dict is None
        assert isinstance(result, int)

        result = THE_MODULE.get_url_parameter_int(None)
        assert result is not None and isinstance(result, int)

    @pytest.mark.xfail 
    @pytest.mark.skipif(SKIP_HINT_TESTS, reason=SKIP_HINT_REASON)
    def test_get_url_parameter_float_type_hints(self):
        param = "param"
        default_value = 0.0
        param_dict = {param: 17.38}

        result = THE_MODULE.get_url_parameter_float(param, default_value, param_dict)

        assert isinstance(param, str)
        assert isinstance(default_value, float)
        assert isinstance(param_dict, dict) or param_dict is None
        assert isinstance(result, float)

        result = THE_MODULE.get_url_parameter_float(None)
        assert result is not None and isinstance(result, float)

    @pytest.mark.xfail 
    @pytest.mark.skipif(SKIP_HINT_TESTS, reason=SKIP_HINT_REASON)
    def test_fix_url_parameters_type_hints(self):
        param = "param"
        param_dict = {param: [17.38, 19.45, 88.88, 16.09]}

        result = THE_MODULE.fix_url_parameters(param_dict)

        assert isinstance(param_dict, dict)
        assert isinstance(result, dict)
        assert not isinstance(result[param], list)
        assert isinstance(result[param], float)

        try:
            result = THE_MODULE.fix_url_parameters(None)
            ## BAD: assert result is not None and isinstance(result, float)
            assert False, "Exception should be raised"
        except:
            ## TODO2: make sure exception triggered by hint violation
            ## NOTE: requires something like Pydantic @validate_call (see test_validate_arguments.py)
            ##   assert system.get_exception()[0] == RuntimeError, "Validation not triggered"
            assert True
            

    @pytest.mark.xfail 
    @pytest.mark.skipif(SKIP_HINT_TESTS, reason=SKIP_HINT_REASON)
    def test_expand_misc_param_type_hints(self):
        misc_dict = {'x': 1, 'y': 2, 'z': 'a=3, b=4'}
        param_name = "z"
        param_dict = {"a":"3", "b":"4"}

        result = THE_MODULE.expand_misc_param(misc_dict, param_name, param_dict)

        assert isinstance(misc_dict, dict)
        assert isinstance(param_dict, dict) or param_dict is None
        assert isinstance(param_name, str)
        assert isinstance(result, dict)

        result = THE_MODULE.expand_misc_param(None, None)
        assert isinstance(result, dict) or result is None
        
    @pytest.mark.xfail
    @pytest.mark.skipif(SKIP_HINT_TESTS, reason=SKIP_HINT_REASON)
    def test__read_file_type_hints(self):
        contents = "Hello World"
        filename = self.create_temp_file(contents)
        as_binary = False
        result = THE_MODULE._read_file(filename, as_binary)

        assert isinstance(filename, str)
        assert isinstance(as_binary, bool)
        assert isinstance(result, str)        

    @pytest.mark.xfail
    @pytest.mark.skipif(SKIP_HINT_TESTS, reason=SKIP_HINT_REASON)
    def test__write_file_type_hints(self):
        data = "Hello World"
        filename = self.create_temp_file(contents="")
        as_binary = False
        # pylint: ignore disable=assignment-from-none
        result = THE_MODULE._write_file(filename, data, as_binary)

        assert isinstance(data, (str, bytes))
        assert isinstance(filename, str)
        assert isinstance(as_binary, bool)
        assert result is None  

    @pytest.mark.xfail
    def test_format_checkbox(self):
        """Verify simple format_checkbox usage"""
        # ex: <input type='hidden' name='fubar' value='off'><label id='fubar-label-id' >Fubar?<input type='checkbox' id='fubar-id' name='fubar'   ></label>"
        field_spec = THE_MODULE.format_checkbox("fubar")
        assert my_re.search(r"<input type='hidden'\s*name='fubar'\s*value='off'><label\s*id='fubar-label-id'\s*>Fubar\?&nbsp;<input\s*type='checkbox'\s*id='fubar-id'\s*name='fubar'\s*></label>",
                            field_spec)
        field_spec = THE_MODULE.format_checkbox("fubar", disabled=True, concat_label=True)
        assert my_re.search(r"<label\s*id='fubar-label-id'\s*>Fubar\?<input\s*type='checkbox'\s*id='fubar-id'\s*name='fubar'\s*disabled\s*></label>",
                            field_spec)

    @pytest.mark.xfail
    def test_format_input_field(self):
        """Verify simple format_input_field usage"""
        ## HACK: ensures that single quotes used in tested result
        #
        field_spec = THE_MODULE.format_input_field("first", label="First:").replace('"', "'")
        assert my_re.search(r"<label\s*id='first-label-id'\s*>First:&nbsp;<input id='first-id'\s*name='first'\s*></label>",
                            field_spec)
        #
        field_spec = THE_MODULE.format_input_field("last", label="Last:", default_value="O'Doe").replace('"', "'")
        assert my_re.search(r"<label\s*id='last-label-id'\s*>Last:&nbsp;<input id='last-id'\s*value='O&#x27;Doe' name='last'\s*></label>",
                            field_spec)
        #
        field_spec = THE_MODULE.format_input_field("age", label="Age:", field_type="number", default_value="19").replace('"', "'")
        assert my_re.search(r"<label\s*id='age-label-id'\s*>Age:&nbsp;<input id='age-id'\s*value='19'\s*name='age'\s*type='number'\s*></label>",
                            field_spec)
        
    @pytest.mark.xfail
    def test_format_url_param(self):
        """Verify format_url_param"""
        THE_MODULE.set_param_dict({"f": "'my dog's fleas'"})
        assert THE_MODULE.format_url_param("f") == '&#x27;my dog&#x27;s fleas&#x27;'
        
    def test_extract_html_images(self):
        """Ensure extract_html_images works as expected"""
        debug.trace(4, "test_extract_html_images()")

        url = 'example.com'
        html = (
            '<!DOCTYPE html>\n'
            '<html>\n'
            '<body>\n'
            '<h2>The target Attribute</h2>\n'
            '<div class="some-class">this is a div</div>\n'
            '<div class="some-class another-class">'
            '<img src="smiley.gif" alt="Smiley face" width="42" height="42" style="border:5px solid black">\n'
            '<img src="some_image.jpg" alt="Some image" width="42" height="42" style="border:5px solid black">\n'
            '<img src="hidden.jpg" alt="this is a hidden image" width="42" height="42" style="display:none">\n'
            '</div>'
            '</body>\n'
            '</html>\n'
        )
        images_urls = [
            f'{url}/smiley.gif',
            f'{url}/some_image.jpg'
        ]

        result = THE_MODULE.extract_html_images(html, url)
        assert result == images_urls
        assert 'hidden.jpg' not in images_urls

    def test_html_to_text(self):
        """Ensure html_to_text works as expected"""
        debug.trace(4, "test_html_to_text()")
        html_path = resolve_mezcla_path(DIMENSIONS_HTML_FILENAME)
        html = system.read_file(html_path)
        text = THE_MODULE.html_to_text(html)
        assert normalize_text(text) == normalize_text(DIMENSIONS_EXPECTED_TEXT)

    def test_format_html_message(self):
        """Ensure html_to_text works as expected"""
        debug.trace(4, "test_html_to_text()")
        html = THE_MODULE.format_html_message("hola", text="josé")
        assert html == "<html lang='en'>  <head>    <title>hola</title>  </head>  <body>    <h3>hola<h3>    josé  </body></html>"

    ## TODO (test for type hint failures):
    ## @pytest.mark.xfail
    ## @pytest.mark.skipif(SKIP_HINT_TESTS, reason=SKIP_HINT_REASON)
    ## def test_download_web_document_type_hints(self):
    ##     ...

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
