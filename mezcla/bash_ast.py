#! /usr/bin/env python3
#
# Produces abstract syntax trees from Bash snippets.
#
# note:
# - Wrapper around bashlex package with AST comparison support added.
#

"""
Support for parsing Bash into abstract syntax trees (ASTs) such as via bash lex

Sample usage:
   {prog} - <<<'sum=$((2 + 2)); if [ $sum -eq 5 ]; then echo "WTH?"; fi'

   IGNORE_ERRORS=1 {prog} - <<<'arr=(1 2 3); echo "${{arr[*]}}"'
"""
## TODO: {prog} <<<'if [[ $((2 + 2)) -eq 5 ]]; then echo "WTH?"; fi'


# Standard modules
## TODO

# Installed modules
import bashlex

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla.my_regex import my_re
from mezcla import system

# Constants
TL = debug.TL
IGNORE_ERRORS = system.getenv_bool("IGNORE_ERRORS", False,
                                   "Ignore unsupported constructs")

class BashAST:
    """Abstract syntax tree for Bash snippets
    Example:
    this_ast = BashAST("if true; then echo hey; fi;")
    other_ast = BashAST("echo hey;")
    this_ast.embedded_in(other_ast)
    """
    # note: Usage based on https://github.com/idank/bashlex

    def __init__(self, snippet=None):
        self.parts = None
        if snippet is not None:
            self.parse(snippet)
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def parse(self, snippet):
        """Parse SNIPPET into AST"""
        debug.trace(4, f"BashAST.parse({snippet!r})")
        kw_args = {}
        if IGNORE_ERRORS:
            kw_args["proceedonerror"] = True
        try:
            self.parts = bashlex.parse(snippet, **kw_args)
        except:
            system.print_exception_info("BashAST.parse")
        result = self.parts
        debug.trace(6, f"BashAST.parse() => {result!r}")
        return result

    def dump(self):
        """Return DUMP of AST"""
        result = ""
        try:
            result = "".join(ast.dump() for ast in self.parts)
        except:
            system.print_exception_info("BashAST.dump")
        return result

    def embedded_in(self, other):
        """Whether AST for current snippet embedded in that for another"""
        # note: implements tree traversal ignoring offsets (i.e., pos attribute)
        return self.ast_embedded_in(self.parts, other.parts)

    @staticmethod
    def ast_embedded_in(ast, other_ast, depth=0):
        """Whether AST is embedded in OTHER (i.e., ignoring offset)"""
        # TODO: ast:List<ast_node_repr>
        indent = (" " * depth)
        debug.trace(8, f"{indent}ast_embedded_in({ast!r}, {other_ast!r}, [d={depth}])")
        embedded = False
        if len(ast) == len(other_ast):
            embedded = all(BashAST.same_ast_node(ast[i], other_ast[i]) for i in range(len(ast)))
        else:
            for sub_node in ast:
                embedded = BashAST.ast_embedded_in(sub_node, other_ast,
                                                   depth=(1 + depth))
                if embedded:
                    break
        if not embedded:
            embedded = (BashAST.ast_node_repr(ast, loose=True)
                        in BashAST.ast_node_repr(other_ast, loose=True))
        debug.trace(7, f"{indent}ast_embedded_in() => {embedded}")
        return embedded
    
    @staticmethod
    def same_ast_node(ast, other_ast):
        """Whether AST node is same as OTHER ignoring offset"""
        # TODO: ast:List<ast_node_repr>
        # example:
        #   CommandNode(pos=(0, 8), parts=[WordNode(pos=(0, 4), word='echo'), WordNode(pos=(5, 8), word='hey'),])
        #   CommandNode(pos=(14, 22), parts=[WordNode(pos=(14, 18), word='echo'), WordNode(pos=(19, 22), word='hey'),])
        same_node = ((ast.kind == other_ast.kind)
                     and (BashAST.ast_node_repr(ast) == BashAST.ast_node_repr(other_ast)))
        debug.trace(7, f"same_ast_node({ast!r}, {other_ast!r}) => {same_node}")
        return same_node

    @staticmethod
    def ast_node_repr(ast, include_pos=False, loose=False):
        """Return representation for node optionally INCLUDing_POS and using LOOSE format"""
        # TODO: ast:List<ast_node_repr>
        node_repr = str(ast)
        if not include_pos:
            node_repr = my_re.sub(r"pos=\(\d+, *\d+\) *", "", node_repr)
        if loose:
            node_repr = my_re.sub(r"^\[(.*)\]$", r"\1", node_repr)
        return node_repr


def main():
    """Entry point"""
    debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")

    # Show simple usage if --help given
    dummy_main_app = Main(description=__doc__.format(prog=gh.basename(__file__)),
                          skip_input=False, manual_input=True)
    debug.assertion(dummy_main_app.parsed_args)

    # Parse Bash snippet from stdin
    snippet = dummy_main_app.read_entire_input()
    ast = BashAST(snippet)
    print(ast.dump())
    return
    
#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_DETAILED)
    main()
