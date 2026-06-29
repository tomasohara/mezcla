This is a customization of the tf-idf package for python [Copyright (c) 2016 elzilrac] available via https://pypi.python.org/pypi/tf-idf. This includes two options enabled via environment variables.
- PENALIZE_SINGLETONS: treat terms with frequency of 1 as 0 
- SPLIT_WORDS: split sentence by word tokens (i.e., \w+) rather than whitespace

note: The complete setup distribution was not included because I didn't want to distribute a setup package with an empty test set!

Tom O'Hara
Fall 2017

................................................................................

Copyright (c) 2016 elzilrac

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
