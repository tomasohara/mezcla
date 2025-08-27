#! /usr/bin/env python3
#
# Notes:
# - This not used: see pyproject.toml instead.
# - Simple installer for subset of scripts under Github
#       https://github.com/tomasohara/misc-utility
# - Based on following:
#       https://stackoverflow.com/questions/1471994/what-is-setup-py
#       https://stackoverflow.com/questions/26528178/right-way-to-set-python-package-with-sub-packages
#
# TODO1:
# - Fix all the 'BAD' items below
# - Also fix keys flagged unknown:
#   $ echo $(python setup.py --help 2>&1 | extract_matches.perl "Unknown distribution option: '(\S+)'")
#   module description_file dist_name email python_requires home_page
#

"""Simple installer"""

from distutils.core import setup

setup(name='Mezcla',
      packages=['mezcla', 'mezcla.tfidf'],
      module="mezcla",
      ## TODO2: import mezcla; version=mezcla.VERSION
      version="1.4.0.5",
      ## BAD: description-file="README.txt",
      description_file="README.txt",
      ## BAD: dist-name="Mezcla",
      dist_name="Mezcla",
      author="Tom O'Hara",
      # TODO3: find out which email key is preferred
      email="tomasohara@gmail.com",
      ## BAD: author-email="tomasohara@gmail.com"
      author_email="tomasohara@gmail.com",
      ## BAD: requires-python=">=3.8",
      python_requires=">=3.8",
      ## TODO4?:
      install_requires=["asttokens", "executing", "six"],
      ## BAD: home-page="https://github.com/tomasohara/Mezcla",
      home_page="https://github.com/tomasohara/Mezcla",
      classifiers=[
          "License :: OSI Approved :: LGPLv3",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.8",
      ],
      description="""
Package with core modules from https://github.com/tomasohara/misc-utility
note: mezcla is Spanish for mixture.
""")
# TODO1: Muchas gracias a Bruno y Tana; <thanks in Tibet> to Aviyan

## BAD:
## NOTE: part of pyproject.toml
## [tool.flit.scripts]
## realpython = "mezcla.__main__:main"
