Note: This is an upgrade of the misc-utility repository with Python 2 support now phased out.

Miscellaneous Python scripts developed over the course of several independent consulting projects. This also includes some code samples I adapted from publicly available source. (The code is not proprietary in nature. For example, it was not "borrowed" from proprietary source files, nor based on proprietary processes.)

Spoiler alter: this is not "Pythonic python": I'm more into R&D than production programming. Nonetheless, there's a some useful scripts here, so I made the repository available. It is public in the spirit of open source software. 

This is a companion script to shell-scripts from Github:
     https://github.com/tomasohara/shell-scripts

This repository is licensed under the GNU Lesser General Public Version 3 (LGPLv3). See LICENSE.txt.

Some style tips:
- Black has been blacklisted over existing modules. Ask to use over new ones.
- Nitpicking pylint exclusions are handled on the command line, so that
  the full pylint output can be checked (a la strict mode). (See the
  python-lint aliases in tomohara-aliases.bash from the shell-scripts-repo.)
- In addition, symbolic names are used (e.g., "C0303" => "trailing-whitespace").

Tom O'Hara
