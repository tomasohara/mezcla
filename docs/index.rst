.. mezcla documentation master file, created by
   sphinx-quickstart on Mon Apr 29 20:47:37 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
   ....
   TODO: automate following:
   $: {
      delete _automodule.list;

      for f in mezcla/*.py; do
      	  b=$(basename $f .py);
       	  perl-echo "  .. automodule:: mezcla.$b\n   :members:\n\n" >> _automodule.list;
      done
   }


Welcome to mezcla's documentation!
==================================

.. toctree::
   :maxdepth: 5
   :glob:

   mezcla/*

   :caption: Contents:


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

  .. automodule:: mezcla._alt_show_bert_representation
   :members:


  .. automodule:: mezcla.analyze_tfidf
   :members:


  .. automodule:: mezcla.audio
   :members:


  .. automodule:: mezcla.bash_ast
   :members:


  .. automodule:: mezcla.bert_multi_classification
   :members:


  .. automodule:: mezcla.bert_text_classification
   :members:


  .. automodule:: mezcla.bing_search
   :members:


  .. automodule:: mezcla.check_html_javascript
   :members:


  .. automodule:: mezcla.compute_tfidf
   :members:


  .. automodule:: mezcla.convert_emoticons
   :members:


  .. automodule:: mezcla.cut
   :members:


  .. automodule:: mezcla.data_utils
   :members:


  .. automodule:: mezcla.debug
   :members:


  .. automodule:: mezcla.evaluate_example_tests
   :members:


  .. automodule:: mezcla.extract_document_text
   :members:


  .. automodule:: mezcla.file_utils
   :members:


  .. automodule:: mezcla.filter_random
   :members:


  .. automodule:: mezcla.format_profile
   :members:


  .. automodule:: mezcla.gensim_test
   :members:


  .. automodule:: mezcla.glue_helpers
   :members:


  .. automodule:: mezcla.gpu_utils
   :members:


  .. automodule:: mezcla.html_utils
   :members:


  .. automodule:: mezcla.__init__
   :members:


  .. automodule:: mezcla.ipython_utils
   :members:


  .. automodule:: mezcla.kenlm_example
   :members:


  .. automodule:: mezcla.keras_param_search
   :members:


  .. automodule:: mezcla.llm_desktop_search
   :members:


  .. automodule:: mezcla.__main__
   :members:


  .. automodule:: mezcla.main
   :members:


  .. automodule:: mezcla.merge_files
   :members:


  .. automodule:: mezcla.merge_notes
   :members:


  .. automodule:: mezcla.misc_utils
   :members:


  .. automodule:: mezcla.my_regex
   :members:


  .. automodule:: mezcla.ngram_tfidf
   :members:


  .. automodule:: mezcla.os_utils
   :members:


  .. automodule:: mezcla.pandas_sklearn
   :members:


  .. automodule:: mezcla._pep8_summarize_example_tests
   :members:


  .. automodule:: mezcla.plot_utils
   :members:


  .. automodule:: mezcla._pylint_summarize_example_tests
   :members:


  .. automodule:: mezcla.python_ast
   :members:


  .. automodule:: mezcla.randomize_lines
   :members:


  .. automodule:: mezcla.rgb_color_name
   :members:


  .. automodule:: mezcla.run_albert_classifier
   :members:


  .. automodule:: mezcla.run_bert_classifier
   :members:


  .. automodule:: mezcla.show_bert_representation
   :members:


  .. automodule:: mezcla.simple_main_example
   :members:


  .. automodule:: mezcla.spacy_nlp
   :members:


  .. automodule:: mezcla.spell
   :members:


  .. automodule:: mezcla._summarize_example_tests
   :members:


  .. automodule:: mezcla.system
   :members:


  .. automodule:: mezcla.sys_version_info_hack
   :members:


  .. automodule:: mezcla.template
   :members:


  .. automodule:: mezcla.text_categorizer
   :members:


  .. automodule:: mezcla.text_processing
   :members:


  .. automodule:: mezcla.text_utils
   :members:


  .. automodule:: mezcla.tpo_common
   :members:


  .. automodule:: mezcla.train_language_model
   :members:


  .. automodule:: mezcla.train_text_categorizer
   :members:


  .. automodule:: mezcla.transpose_data
   :members:


  .. automodule:: mezcla.unittest_wrapper
   :members:


  .. automodule:: mezcla.xml_utils
   :members:


