from protected_field import ProtectedField


class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = []
        self.parent = parent
        self.is_focused = False
        self.style = ProtectedField()
        self.animations = {}
        self.layout_object = None

    def __repr__(self) -> str:
        return repr(self.text)
