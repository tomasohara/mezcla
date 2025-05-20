#! /usr/bin/env python3
#
# Matrix multiply comparison via Stack Overflow:
#    https://stackoverflow.com/questions/36526708/comparing-python-numpy-numba-and-c-for-matrix-multiplication
# Now extended to handle CUDA via Numba, based on following:
#    https://github.com/nyu-cds/courses/blob/master/code/mandelbrot_gpu.py
#
# Note:
# - For background, see
#    https://nyu-cds.github.io/python-numba/05-cuda
#
# TODO:
# - Add in some of the optimizaitons suggested.
#

"""Matrix multiplication for benchmarking"""

# Standard modules
import random

# installed modules
import numpy as np
import numba
from numba import cuda

# Local modules
from mezcla import debug
from mezcla.main import Main
from mezcla import misc_utils
from mezcla import system

# Constants
NUMPY_ARG = "numpy"
NUMBA_ARG = "numba"
PYTHON_ARG = "python"
CUDA_ARG = "cuda"
ROWS_ARG = "rows"
COLS_ARG = "cols"
K = 11

# Environment options
SKIP_CUDA = system.getenv_bool(
    "SKIP_CUDA", False,
    description="Don't use CUDA JIT")
MATRIX_SIZE = system.getenv_int(
    "MATRIX_SIZE", 10,
    description="Default size for matrix row and column")
NUM_ROWS = system.getenv_int(
    "NUM_ROWS", MATRIX_SIZE,
    description="Number of rows in matrix")
NUM_COLS = system.getenv_int(
    "NUM_COLS", MATRIX_SIZE,
    description="Number of cols in matrix")

#-------------------------------------------------------------------------------

if SKIP_CUDA:
    cuda.grid = lambda x: (0, 0)

def dot_py(A, B, C, label):
    """(Regular) Python matrix multiplication
    Note: C must be shaped beforehand
    Hack: if label an integer, 1 is A, 2 is B, etc.
    """
    # note: transformed to Numba and CUDA versions via JIT below
    is_cuda = (label == K)
    m, n = A.shape
    p = B.shape[1]
    if isinstance(label, int):
        label = "ABCDEFGHIJKLMNOPQRSTUVQXYZ"[label - 1]
        #        123456789-123456789-123456
    r_lower = 0
    r_upper_plus1 = m
    c_lower = 0
    c_upper_plus1 = p
    if is_cuda:
        x, y = cuda.grid(2)             # pylint: disable=no-value-for-parameter
        r_lower = x
        r_upper_plus1 = x + 1
        c_lower = y
        c_upper_plus1 = y + 1
    if r_lower >= C.shape[0] or c_lower >= C.shape[1]:
        if (debug.trace_level >= 5):
            print("FYI: Invalid dimensions: {(r_lower, c_lower)}")
        return

    for i in range(r_lower, r_upper_plus1):
        for j in range(c_lower, c_upper_plus1):
            # TODO2: temp = 0; ...;  C[i, j] = temp
            C[i, j] = 0
            for k in range(n):                    # MxN NxP    (i.e., RxT TxC)
                C[i, j] += A[i, k] * B[k, j]
    # note: due to numba/cuda restrictions, must reproduce print_array here
    if (debug.trace_level >= 6):
        qual = ("" if not is_cuda else ("[" + str(x) + "," + str(y) + "]"))
        print(label + qual + ":")
        for r in range(r_lower, r_upper_plus1):
            row = ""
            for c in range(c_lower, c_upper_plus1):
                row += str(C[r, c]) + " "
        print(row)
    return

def print_array(arr: np.ndarray, label: str, level: int):
    """Print 2D array ARR to stdout prefixed by LABEL if trace LEVEL or higher
    note: traces excerpt to stderr at LEVEL-1
    """
    # note: Uses stdout due to CUDA quirk with stderr (for consistency)
    debug.trace_expr(level - 1, arr, prefix=f"{label}:\n")
    if (debug.trace_level >= level):
        print(label + ":")
        for r in range(0, arr.shape[0]):
            row = ""
            for c in range(0, arr.shape[1]):
                row += str(arr[r, c]) + " "
            print(row)
    

def dot_numpy(A, B, C, label):
    """Numpy-based matrix multiplication"""
    ## TODO2: see if numpy has alternative with 3 args
    C_prime = np.dot(A, B)
    for i in range(0, A.shape[0]):
        for j in range(0, B.shape[1]):
            C[i, j] = C_prime[i, j]
    print_array(C, label, level=6)
    return


# Numba: Same as the Python one, but compiled just in time
#
# TODO: parameterize type as in numba_test.py
float64 = numba.float64
## OLD: dot_numba = numba.jit("void(float64[:,:], float64[:,:], float64[:,:], int64)", nopython=True)(dot_py)
## OLD: dot_numba = numba.jit(nopython=True)(dot_py)
# note: allows python for sake of uniformity: this is far from production (i.e., just a testbed)
dot_numba = numba.jit(nopython=False)(dot_py)
dot_cuda = None
if not SKIP_CUDA:
    ## BAD: dot_cuda = cuda.jit("void(float64[:,:], float64[:,:], float64[:,:], int64)")(dot_py)
    dot_cuda = cuda.jit()(dot_py)

#-------------------------------------------------------------------------------

class Script(Main):
    """Input processing class"""
    # TODO: -or-: """Adhoc script class (e.g., no I/O loop, just run calls)"""
    numpy_arg = True
    python_arg = False
    numba_arg = True
    cuda_arg = True
    num_rows = NUM_ROWS
    num_cols = NUM_COLS

    def setup(self):
        """Check results of command line processing"""
        debug.trace_fmtd(5, "Script.setup(): self={s}", s=self)
        self.numpy_arg = self.get_parsed_option(NUMPY_ARG, self.numpy_arg)
        self.numba_arg = self.get_parsed_option(NUMBA_ARG, self.numba_arg)
        self.python_arg = self.get_parsed_option(PYTHON_ARG, self.python_arg)
        self.cuda_arg = self.get_parsed_option(CUDA_ARG, self.cuda_arg)
        # TODO: self.TODO_filename = self.get_parsed_argument(TODO_FILENAME)
        debug.trace_object(5, self, label="Script instance")

    def random_vector(self, num):
        """Return random vector of length NUM"""
        result = [random.random() for _i in range(num)]
        debug.trace(6, f"random_vector() => {result}")
        return result

    def random_array(self):
        """Return random 2D array of size self.num_cols x self.num_cols"""
        array_data = [self.random_vector(self.num_cols) for _r in range(self.num_rows)]
        result = np.array(array_data)
        debug.trace(6, f"random_array() => {result}")
        return result

    def run_main_step(self):
        """Main processing step"""
        debug.trace_fmtd(5, "Script.run_main_step(): self={s}", s=self)

        # Create matrices and placeholder for result
        a = self.random_array()
        b = self.random_array()
        print_array(a, "a", level=6)
        print_array(b, "b", level=6)
        c = np.zeros((a.shape[0], b.shape[1]))
        c_alt = np.zeros((a.shape[0], b.shape[1]))
        debug.assertion(self.numpy_arg)

        # Run the various matrix multiplication methods
        ## OLD: dot_numpy(a, b, c)
        numpy_ms = python_ms = numba_ms = cuda_ms = -1
        numpy_ms = misc_utils.time_function(dot_numpy, a, b, c, "numpy c")
        if self.python_arg:
            python_ms = misc_utils.time_function(dot_py, a, b, c_alt, "python c")
            debug.trace_expr(5, c_alt, prefix="python c:\n")
            ## OLD: debug.assertion(np.array_equal(c_alt, c))
            debug.assertion(np.allclose(c_alt, c))
        if self.numba_arg:
            numba_ms = misc_utils.time_function(dot_numba, a, b, c_alt, 3)
            debug.trace_expr(5, c_alt, prefix="numba c:\n")
            ## OLD: debug.assertion(np.array_equal(c_alt, c))
            debug.assertion(np.allclose(c_alt, c))
        if self.cuda_arg and dot_cuda:
            def invoke_dot_cuda(a, b, c, label):
                """Calls CUDA function with grid and block dimensions"""
                # TODO2: summarize ChatGPT explanation
                block_size = 32                     # 32x32 threads per block
                grid_dim = ((self.num_rows + block_size - 1) // block_size,
                            (self.num_cols + block_size - 1) // block_size)
                block_dim = (block_size, block_size)
                dot_cuda[grid_dim, block_dim](a, b, c, label)
            cuda_ms = misc_utils.time_function(invoke_dot_cuda, a, b, c_alt, K)
            debug.trace_expr(5, c_alt, prefix="cuda c:\n")
            ## OLD: debug.assertion(np.array_equal(c_alt, c))
            debug.assertion(np.allclose(c_alt, c))

        # Show timing results
        results = [("numpy", numpy_ms), ("numba", numba_ms), ("python", python_ms), ("cuda", cuda_ms)]
        for (method, ms) in results:
            print(f"{method}\t{ms}ms")

#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    debug.trace_current_context(level=debug.QUITE_DETAILED)
    app = Script(
        description=__doc__,
        skip_input=False,
        manual_input=True,
        boolean_options=[NUMPY_ARG, NUMBA_ARG, PYTHON_ARG, CUDA_ARG],
        int_options=[ROWS_ARG, COLS_ARG])
    app.run()

