from dom_utils import is_focusable
from text import Text


class AccessibilityNode:
    def __init__(self, node) -> None:
        self.node = node
        self.children = []
        self.role = "none"
        self.text = ""
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

        if self.role == "StaticText":
            self.text = repr(self.node.text)
        elif self.role == "focusable text":
            self.text = "Focusable text: " + self.node.text
        elif self.role == "focusable":
            self.text = "Focusable element"
        elif self.role == "textbox":
            value = ""
            if "value" in self.node.attributes:
                value = self.node.attributes["value"]
            elif (
                self.node.tag != "input"
                and self.node.children
                and isinstance(self.node.children[0], Text)
            ):
                value = self.node.children[0].text
            self.text = "Input box: " + value
        elif self.role == "button":
            self.text = "Button"
        elif self.role == "link":
            self.text = "Link"
        elif self.role == "alert":
            self.text = "Alert"
        elif self.role == "document":
            self.text = "Document"

        if self.node.is_focused:
            self.text += " is focused"

    def build_internal(self, child_node):
        child = AccessibilityNode(child_node)
        if child.role != "none":
            self.children.append(child)
            child.build()
        else:
            for grandchild_node in child_node.children:
                self.build_internal(grandchild_node)

    def __repr__(self):
        return "AccessibilityNode(node={}, role={}, text={}".format(
            str(self.node), self.role, self.text
        )
