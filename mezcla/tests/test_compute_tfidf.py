#! /usr/bin/env python3
#
# Test(s) for ../compute_tfidf.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_compute_tfidf.py
#
#--------------------------------------------------------------------------------
# Sample input and output
#
# - input:
#   Jul 26, 2022 ... 17 Top-Rated Tourist Attractions in Argentina \u00b7 1. Iguaz\u00fa Falls \u00b7 2. Perito Moreno Glacier \u00b7 3. Recoleta, La Boca, and Tango in Buenos Aires \u00b7 4\u00a0...
#   Oct 2, 2023 ... Discover Argentine Patagonia's top attractions, best hikes, and more. Visit the dramatic landscapes of one of Earth's popular trekking\u00a0...
#   Jun 15, 2021 ... Top 10 Argentina Tourist Attractions You Have To See \u00b7 Recoleta Cemetery, Buenos Aires \u00b7 Caminito \u00b7 The Mosque-Cathedral of C\u00f3rdoba \u00b7 Quebrada\u00a0...
#   Top Attractions in Argentina \u00b7 1. Teatro Colon \u00b7 2. Puerto Madero \u00b7 3. Recoleta \u00b7 4. Iguazu Falls \u00b7 5. Cementerio de la Recoleta \u00b7 6. Garganta del Diablo \u00b7 7.
#   Argentina's best sights and local secrets from travel experts you can trust.
#   Apr 13, 2022 ... View All Trips \u00b7 Front view of the Perito Moreno Glacier | \u00a9 pclvv/Flickr \u00b7 | \u00a9 Det-anan/Shutterstock \u00b7 Quebrada de Humahuaca | \u00a9 Randal\u00a0...
#   Dec 8, 2017 ... Your trip to Salta is NOT complete without taking a leisurely stroll to Plaza 9 de Julio. This square is at the very heart of the city and is\u00a0...
#   Mar 28, 2023 ... 7 places to visit in Argentina that will make you never want to leave \u00b7 1. The Patagonia region \u00b7 2. The town of El Calafate \u00b7 3. Los Glaciares\u00a0...
#   Mar 27, 2022 ... 10 Things to do in Mendoza, Argentina.
#   Nov 22, 2023 ... Take care on public transport and in tourist areas or crowded places. Thefts and robberies in Buenos Aires and other major cities are increasing\u00a0...
#   
# - output:
##   TODO2: revise (and show all values used in TF-IDF calculation, etc., as follows):
##      Term                             TFreq     DFreq     TF        IDF       TF-IDF   
##      apr 13                           1.000     1.000     0.045     2.303     0.105    
#
#   1 [tests/resources/argentinian-attraction-snippets.list:1]
#   term                             TF-IDF   
#   jul 26                           0.005    
#   17 top-rated                     0.005    
#   top-rated tourist                0.005    
#   
#   2 [tests/resources/argentinian-attraction-snippets.list:2]
#   term                             TF-IDF   
#   oct 2                            0.003    
#   discover argentine               0.003    
#   patagonia's top                  0.003    
#   
#   3 [tests/resources/argentinian-attraction-snippets.list:3]
#   term                             TF-IDF   
#   jun 15                           0.005    
#   top 10                           0.005    
#   argentina tourist                0.005    
#   
#   4 [tests/resources/argentinian-attraction-snippets.list:4]
#   term                             TF-IDF   
#   top attractions in               0.008    
#   top attractions in argentina     0.008    
#   teatro colon                     0.008    
#   
#   5 [tests/resources/argentinian-attraction-snippets.list:5]
#   term                             TF-IDF   
#   argentina's best                 0.005    
#   sights and                       0.005    
#   local secrets                    0.005    
#   
#   6 [tests/resources/argentinian-attraction-snippets.list:6]
#   term                             TF-IDF   
#   apr 13                           0.008    
#   view all                         0.008    
#   front view                       0.008    
#   
#   7 [tests/resources/argentinian-attraction-snippets.list:7]
#   term                             TF-IDF   
#   dec 8                            0.002    
#   your trip                        0.002    
#   to salta                         0.002    
#   
#   8 [tests/resources/argentinian-attraction-snippets.list:8]
#   term                             TF-IDF   
#   mar 28                           0.003    
#   7 places                         0.003    
#   to visit                         0.003    
#   
#   9 [tests/resources/argentinian-attraction-snippets.list:9]
#   term                             TF-IDF   
#   mar 27                           0.017    
#   10 things                        0.017    
#   to do                            0.017    
#   
#   10 [tests/resources/argentinian-attraction-snippets.list:10]
#   term                             TF-IDF   
#   nov 22                           0.002    
#   take care                        0.002    
#   on public                        0.002    
#

"""Tests for compute_tfidf module"""

# Standard packages
## NOTE: this is empty for now

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla.my_regex import my_re
import mezcla.glue_helpers as gh

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.compute_tfidf as THE_MODULE

class TestComputeTfidf(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def test_show_usage_and_quit(self):
        """Ensure show_usage_and_quit works as expected"""
        debug.trace(4, "test_show_usage_and_quit()")
        output = self.run_script("--help")
        self.do_assert("Derives TF-IDF" in output)
        self.do_assert("MIN_NGRAM_SIZE" in output)

    def test_get_suffix1_prefix2(self):
        """Ensure get_suffix1_prefix2 works as expected"""
        debug.trace(4, "test_get_suffix1_prefix2()")
        assert THE_MODULE.get_suffix1_prefix2(["my", "dog"], ["dog", "has"]) == ["dog"]
        assert not THE_MODULE.get_suffix1_prefix2(["a", "b", "c"], ["b", "d"])

    def test_terms_overlap(self):
        """Ensure terms_overlap works as expected"""
        debug.trace(4, "test_terms_overlap()")
        assert THE_MODULE.terms_overlap("ACME Rocket Research", "Rocket Research Labs") == "Rocket Research"
        assert not THE_MODULE.terms_overlap("Rocket Res", "Rocket Research")

    def test_is_subsumed(self):
        """Ensure is_subsumed works as expected"""
        debug.trace(4, "test_is_subsumed()")
        assert THE_MODULE.is_subsumed("White House", ["The White House", "Congress", "Supreme Court"])
        assert THE_MODULE.is_subsumed("White House", ["White Houses"])

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_data_file(); self={self}")
        data_file = gh.resolve_path(gh.form_path("resources", "argentinian-attraction-snippets.txt"))
        output = self.run_script(options="--text", env_options="MIN_NGRAM_SIZE=2 MAX_NGRAM_SIZE=4",
                                 data_file=data_file)
        ## TODO3: review calculations
        self.do_assert(my_re.search(r"^\s*4.*teatro colon\s+0.128", output.strip(),
                                    flags=my_re.MULTILINE|my_re.DOTALL))
        self.do_assert(my_re.search(r"^\s*5.*local secrets\s+0.077", output.strip(),
                                    flags=my_re.MULTILINE|my_re.DOTALL))
        self.do_assert(my_re.search(r"^\s*6.*the perito moreno\s+0.105", output.strip(),
                                    flags=my_re.MULTILINE|my_re.DOTALL))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_csv_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_csv_file(); self={self}")

        # Run unigram TF/IDF over the file
        ## TODO3: derive the CSV file from the text file
        data_file = gh.resolve_path(gh.form_path("resources", "argentinian-attraction-snippets.csv"))
        output = self.run_script(options="--csv --show-all --num-top-terms 100", env_options="MIN_NGRAM_SIZE=1 MAX_NGRAM_SIZE=1",
                                 data_file=data_file)
        # Covert multiple spaces to one
        output = my_re.sub(r"  +", " ", output.strip())
        docs = output.split("\n\n")

        # Check for following output (ignoring spacing):
        #   term       TFreq  DFreq  TF     IDF    TF-IDF
        #   argentina  1.000  5.000  0.040  0.693  0.028
        debug.trace_values(5, docs)
        self.do_assert(all(("term TFreq DFreq TF IDF TF-IDF" in docs[i])
                           for i in range(10)))
        self.do_assert("argentina 1.000 5.000 0.040 0.693 0.028" in docs[0])
        return


if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
