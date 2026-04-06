from dom_utils import CSS_PROPERTIES
from protected_field import ProtectedField


class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent
        self.is_focused = False
        self.style = dict(
            [(property, ProtectedField(self, property)) for property in CSS_PROPERTIES]
        )
        self.animations = {}
        self.layout_object = None

    def __repr__(self) -> str:
        return "<" + self.tag + ">"
