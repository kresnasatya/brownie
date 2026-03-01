from dom_utils import is_focusable
from text import Text


class AccessibilityNode:
    def __init__(self, node) -> None:
        self.node = node
        self.children = []
        self.role = "none"
        if isinstance(node, Text):
            if is_focusable(node.parent):
                self.role = "focusable text"
            else:
                self.role = "StaticText"
        else:
            if "role" in node.attributes:
                self.role = node.attributes["role"]
            elif node.tag == "a":
                self.role = "link"
            elif node.tag == "input":
                self.role = "textbox"
            elif node.tag == "button":
                self.role = "button"
            elif node.tag == "html":
                self.role = "document"
            elif is_focusable(node):
                self.role = "focusable"

    def build(self):
        for child_node in self.node.children:
            self.build_internal(child_node)

    def build_internal(self, child_node):
        child = AccessibilityNode(child_node)
        if child.role != "none":
            self.children.append(child)
            child.build()
        else:
            for grandchild_node in child_node.children:
                self.build_internal(grandchild_node)

    def __repr__(self, indent=0):
        return (" " * indent + "role=" + self.role + "\n"
            + "".join([child.__repr__(indent + 2)
                       for child in self.children]))
