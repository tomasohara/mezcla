#! /usr/bin/env python3
#
# Test(s) for ../html_utils.py
#
# Notes:
# - Fill out TODO's below. Use numbered tests to order (e.g., test_1_usage).
# - TODO: If any of the setup/cleanup methods defined, make sure to invoke base
#   (see examples below for setUp and tearDown).
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_html_utils.py
#

"""Tests for html_utils module"""

# Standard packages
import re
import os

# Installed packages
import pytest
## OLD: import bs4

# Local packages
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import debug
from mezcla import system
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
## TODO: template => new name
import mezcla.html_utils as THE_MODULE

# Environment options
TEST_SELENIUM = system.getenv_bool("TEST_SELENIUM", False,
                                   "Include tests requiring selenium")

class TestHtmlUtils(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    scrappycito_url = "http://www.scrappycito.com"
    # TODO: use_temp_base_dir = True            # treat TEMP_BASE as directory
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_browser(self):
        """Ensure get_browser() works as expected"""
        debug.trace(4, "test_get_browser()")
        assert False, "TODO: code test"

    def test_get_url_parameter_value(self):
        """Ensure get_url_parameter_value works as expected"""
        debug.trace(4, "test_get_url_parameter_value()")
        save_user_parameters = THE_MODULE.user_parameters
        THE_MODULE.user_parameters = {}
        assert THE_MODULE.get_url_parameter_value("fubar", None) is None
        assert THE_MODULE.get_url_parameter_value("fubar", None, {"fubar": "fu"}) == "fu"
        THE_MODULE.user_parameters = {"fubar": "bar"}
        assert THE_MODULE.get_url_parameter_value("fubar", None) == "bar"
        assert THE_MODULE.get_url_parameter_value("fubar", None, {"fubar": "fu"}) == "fu"
        THE_MODULE.user_parameters = save_user_parameters
        return

    def test_get_inner_text(self):
        """Verify that JavaScript fills in window dimensions
        Note: requires selenium"""
        debug.trace(4, "test_get_inner_text()")
        if not TEST_SELENIUM:
            debug.trace(4, "Ignoring test_get_inner_text as selenium required")
            return
        html_filename = "simple-window-dimensions.html"
        html_path = gh.resolve_path(html_filename)
        url = ("file:" + system.absolute_path(html_path))
        # TODO: use direct API call to return unrendered text
        unrendered_text = gh.run(f"lynx -dump {url}")
        debug.trace_expr(5, unrendered_text)
        assert re.search(r"Browser dimensions: \?", unrendered_text)
        rendered_text = THE_MODULE.get_inner_text(url)
        debug.trace_expr(5, rendered_text)
        assert re.search(r"Browser dimensions: \d+x\d+", rendered_text)

    def test_get_inner_html(self):
        """Verify that JavaScript fills in window dimensions
        Note: requires selenium"""
        debug.trace(4, "test_get_inner_html()")
        if not TEST_SELENIUM:
            debug.trace(4, "Ignoring test_get_inner_html as selenium required")
            return
        html_filename = "simple-window-dimensions.html"
        html_path = gh.resolve_path(html_filename)
        url = ("file:" + system.absolute_path(html_path))
        # TODO: use direct API call to return unrendered text
        unrendered_html = gh.run(f"lynx -source {url}")
        debug.trace_expr(5, unrendered_html)
        assert re.search(
            r"<li>Browser dimensions:\s*<span.*>\?\?\?</span></li>",
            unrendered_html,
            )
        rendered_html = THE_MODULE.get_inner_html(url)
        debug.trace_expr(5, rendered_html)
        assert re.search(
            r"<li>Browser dimensions:\s*<span.*>\d+x\d+</span></li>",
            rendered_html,
            )

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_inner_html_alt(self):
        """Alternative test of get_inner_html"""
        debug.trace(4, f"TestIt.test_get_inner_html_alt(); self={self}")
        output = THE_MODULE.get_inner_html(self.scrappycito_url)
        self.do_assert(not my_re.search(r"sign.out", output.strip(), flags=my_re.IGNORECASE))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_run_script_for_inner_html(self):
        """Test of getting inner HTML via script invocation"""
        debug.trace(4, f"TestIt.test_run_script_for_inner_html(); self={self}")
        output = self.run_script(options=f"--inner --stdout {self.scrappycito_url}", data_file=self.temp_file)
        self.do_assert(not my_re.search(r"sign.out", output.strip(), flags=my_re.IGNORECASE))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_document_ready(self):
        """Ensure document_ready() works as expected"""
        debug.trace(4, "test_document_ready()")
        assert False, "TODO: code test"

    def test_escape_html_value(self):
        """Ensure escape_html_value() works as expected"""
        debug.trace(4, "test_escape_html_value()")
        # note: this test is the same as system.test_escape_html_text
        assert THE_MODULE.escape_html_value("<2/") == "&lt;2/"
        assert THE_MODULE.escape_html_value("Joe's hat") == "Joe&#x27;s hat"

    def test_unescape_html_value(self):
        """Ensure unescape_html_value() works as expected"""
        debug.trace(4, "test_unescape_html_value()")
        # note: this test is the same as test_system.test_unescape_html_text
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
        assert THE_MODULE.get_param_dict('not-found-status') == 'not-found-status'
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
        assert THE_MODULE.get_url_param('bad-request-status', default_value='400') == '400'
        assert THE_MODULE.get_url_param('default-body', escaped=True) == 'Joe&#x27;s hat'

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_url_param_checkbox_spec(self):
        """Ensure get_url_param_checkbox_spec() works as expected"""
        debug.trace(4, "test_get_url_param_checkbox_spec()")
        param_dict = {"check_1": "on", "check_2": "off","check_3": "True",
                                    "check_4": False, "check_5": 1}

        # Test multiple positive cases
        assert THE_MODULE.get_url_param_checkbox_spec("check_1", param_dict=param_dict)
        assert THE_MODULE.get_url_param_checkbox_spec("check_3", param_dict=param_dict)
        assert THE_MODULE.get_url_param_checkbox_spec("check_5", param_dict=param_dict)

        # test non-checked and non-existent check cases
        assert not THE_MODULE.get_url_param_checkbox_spec("check_2", param_dict=param_dict)
        assert not THE_MODULE.get_url_param_checkbox_spec("check_4", param_dict=param_dict)
        assert not THE_MODULE.get_url_param_checkbox_spec("non_check", param_dict=param_dict)

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
        debug.set_level(3)
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

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_old_download_web_document(self):
        """Ensure old_download_web_document() works as expected"""
        ## NOTE: Currently fails if UTF-8 error occurs
        debug.trace(4, "test_old_download_web_document()")
        assert "<!doctype html>" in THE_MODULE.old_download_web_document("https://www.google.com")

    def test_download_web_document(self):
        """Ensure download_web_document() works as expected"""
        debug.trace(4, "test_download_web_document()")
        assert "currency" in THE_MODULE.download_web_document("https://simple.wikipedia.org/wiki/Dollar")
        assert THE_MODULE.download_web_document("www. bogus. url.html") is None

    def test_test_download_html_document(self):
        """Ensure test_download_html_document() works as expected"""
        debug.trace(4, "test_test_download_html_document()")
        assert "Google" in THE_MODULE.test_download_html_document("www.google.com")
        assert "Tomás" not in THE_MODULE.test_download_html_document("http://www.tomasohara.trade", encoding="big5")

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_download_html_document(self):
        """Ensure download_html_document() works as expected"""
        debug.trace(4, "test_download_html_document()")

        # Set tmp_dir and filename for testing
        tmp_dir = system.getenv("TMP")
        filename = "test_download_file"

        # Assert file is downloaded and created in tmp_dir
        THE_MODULE.download_html_document("http://www.tomasohara.trade", download_dir=tmp_dir, filename=filename)
        assert filename in system.read_directory(tmp_dir)

        # Assert exception report is printed when not Ignore
        try :
            _ = THE_MODULE.download_html_document("", ignore=False)
        except Exception as _:
            pass
        err = self.get_stderr()
        assert "Error during retrieve_web_document" in err

        # Assert exception report is not printed when Ignore
        self.clear_stderr()
        try :
            _ = THE_MODULE.download_html_document("", ignore=True)
        except Exception as _:
            pass
        err = self.get_stderr()
        assert "Error during retrieve_web_document" not in err




    @pytest.mark.xfail                   # TODO: remove xfail
    def test_download_binary_file(self):
        """Ensure download_binary_file() works as expected"""
        debug.trace(4, "test_download_binary_file()")
        binary_doc = THE_MODULE.download_binary_file(url="www.tomasohara.trade")
        non_binary_doc = THE_MODULE.download_web_document(url="www.tomasohara.trade")
        assert re.search(b"Scrappy.*Cito", binary_doc)
        assert bytes(non_binary_doc, encoding="UTF-8") == binary_doc


    def test_retrieve_web_document(self):
        """Ensure retrieve_web_document() works as expected"""
        debug.trace(4, "test_retrieve_web_document()")
        assert re.search("Scrappy.*Cito", THE_MODULE.retrieve_web_document("www.tomasohara.trade"))

    def test_init_BeautifulSoup(self):
        """Ensure init_BeautifulSoup() works as expected"""
        debug.trace(4, "test_init_BeautifulSoup()")
        THE_MODULE.BeautifulSoup = None
        THE_MODULE.init_BeautifulSoup()
        assert THE_MODULE.BeautifulSoup

    def test_extract_html_link(self):
        """Ensure extract_html_link() works as expected"""
        debug.trace(4, "test_extract_html_link()")

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

        # NOTE that the last two urls has a extra '/'.
        ## TODO: check if the extra '/' in the last two urls are correct.
        all_urls = [
            'https://www.anothersite.io/',
            'https://www.example.com/',
            'https://www.example.com/sopport',
            'https://www.subdomain.example.com/',
            'https://www.example.com.br/',
            'http:///www.subdomain.example.com/sitemap.xml',
            'https://www.example.com//home.html',
        ]

        # Test extract all urls from html
        assert THE_MODULE.extract_html_link(html, url='https://www.example.com', base_url='http://') == all_urls

        # Test base_url none
        ## TODO: this assertion is returning, need to be solved:
        ##      https://www.example.com//www.subdomain.example.com/sitemap.xml
        ## assert THE_MODULE.extract_html_link(html, url='https://www.example.com') == all_urls

    @pytest.mark.xfail
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

    @pytest.mark.xfail
    def test_document_ready_alt(self):
        URL_VALID = "https://duckduckgo.com"
        assert (THE_MODULE.document_ready(URL_VALID))
        assert not THE_MODULE.document_ready(self.scrappycito_url)
        ## Exception raised:
        # E       selenium.common.exceptions.JavascriptException: Message: TypeError: document.body is null
        # E       Stacktrace:
        # E       @http://www.scrappycito.com:9330/:2:7
        # E       @http://www.scrappycito.com:9330/:3:8
        # /home/zavee/.local/lib/python3.10/site-packages/selenium/webdriver/remote/errorhandler.py:229: JavascriptException

    @pytest.mark.xfail
    def test_set_param_dict_alt(self):
        param_dict = {
            1: "a+b+c",
            2: "a%2b%2c%2"
        }
        THE_MODULE.set_param_dict(param_dict)
        assert THE_MODULE.user_parameters == param_dict

    @pytest.mark.xfail
    def test_set_param_dict_type_hints(self):
        param_dict = str({1: "a+b+c", 2: "a%2b%2c%2"})
        THE_MODULE.set_param_dict(param_dict)
        assert not isinstance(THE_MODULE.user_parameters, dict)
        assert len(THE_MODULE.user_parameters) > 2

    @pytest.mark.xfail    
    def test_get_param_dict_type_hints(self):
        param_dict = str({
            "p1": "a+b+c",
            "p2": "a%2b%2c%2"
        })
        result = THE_MODULE.get_param_dict(param_dict=param_dict)
        assert not isinstance(result, dict)

    @pytest.mark.xfail 
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
    def test_fix_url_parameters_type_hints(self):
        param = "param"
        param_dict = {param: [17.38, 19.45, 88.88, 16.09]}

        result = THE_MODULE.fix_url_parameters(param_dict)

        assert isinstance(param_dict, dict)
        assert isinstance(result, dict)
        assert not isinstance(result[param], list)  

        result = THE_MODULE.fix_url_parameters(None)
        assert result is not None and isinstance(result, float)

    @pytest.mark.xfail 
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
    def test__read_file_type_hints(self):
        contents = "Hello World"
        filename = self.create_temp_file(contents)
        as_binary = False
        result = THE_MODULE._read_file(filename, as_binary)

        assert isinstance(filename, str)
        assert isinstance(as_binary, bool)
        assert isinstance(result, str)        

    @pytest.mark.xfail
    def test__write_file_type_hints(self):
        data = "Hello World"
        filename = self.create_temp_file(contents="")
        as_binary = False
        result = THE_MODULE._write_file(filename, data, as_binary)

        assert isinstance(data, (str, bytes))
        assert isinstance(filename, str)
        assert isinstance(as_binary, bool)
        assert result is None  
        
    # @pytest.mark.xfail
    # def test_download_web_document_type_hints(self):

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
