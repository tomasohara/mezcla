#! /usr/bin/env python
#
# Miscellaneous XML utility functions
#
#--------------------------------------------------------------------------------
# Notes:
# - The tail text is not intuitive, including what would seem to belong to the
#   parent node. Via https://docs.python.org/3/library/xml.etree.elementtree.html:
# 
#   <a>                                     a.text = a.tail = None
#     <b>1                  b.text
#       <c>2                c.text
#         <d/>
#         3                 d.tail
#       </c>
#     </b>
#     4                     b.tail
#   </a>
# 
# 
# text: text between element’s start tag and its first child or end tag
# tail: text between the element’s end tag and the next tag
# 

"""XML utility functions"""

# Standard packages
import sys
import xml.etree.ElementTree as ET

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system


def parse_xml(xml_text):
    """Parse XML_text, returning root node"""
    try:
        tree = ET.ElementTree(ET.fromstring(xml_text))
        root = tree.getroot()
        debug.trace_object(5, root, "xml root")
    except:
        system.print_exception_info("parse_xml")
    debug.trace(4, f"parse_xml({xml_text}) => {root}")
    return root


def etree_to_dict(node):
    """Convert XML parse at NODE to dict"""
    d = {node.tag : list(map(etree_to_dict, list(node)))}
    d.update(('@' + k, v) for k, v in node.attrib.items())
    d['text'] = node.text
    d['tail'] = node.tail
    d['inner'] = "".join(node.itertext())
    return d


def get_xml_text(node, depth=0):
    """Get all text for XML node at ROOT"""
    # TODO: get_xml_text => get_xml_tree_text???
    indent = "    " * depth if __debug__ else ""
    debug.trace(5, f"{indent}get_xml_text({node}, {depth})")
    debug.trace(4, f'[l] {node.tag + ": "}', no_eol=True)
    text = ("\t" * depth) + node.tag + ": "
    if node.text:
        debug.trace(4, f"[n] {node.text}", no_eol=True)
        text += node.text
    for child in node:
        text += "\n" + get_xml_text(child, 1 + depth)
    if node.tail:
        debug.trace(4, f"[t] {node.tail}", no_eol=True)
        text += "\n" + ("\t" * depth) + node.tail
    debug.trace(6, f"{indent}get_xml_text() => {text}")
    return text

#...............................................................................

def main(args):
    """Entry point for script"""
    xml_text = "<a><b>1<c>2<d/>3</c></b>4</a>"
    if (len(args) > 1):
        xml_text = system.read_file(args[1])

    # Show input
    print("Input:")
    print(gh.indent(xml_text))
    print()

    # Show text as parse tree
    parsed_xml_text = get_xml_text(parse_xml(xml_text))
    debug.trace(4, f"\nlen={len(parsed_xml_text)}")
    print("XML parse tree")
    print(gh.indent_lines(parsed_xml_text))
    return

if __name__ == '__main__':
    system.print_error("Warning: Not intended for direct invocation.")
    system.print_error("A simle test follows.")
    main(sys.argv)
