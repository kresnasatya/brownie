class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = []
        self.parent = parent
        self.is_focused = False
        self.style = {}
        self.animations = {}

    def __repr__(self) -> str:
        return repr(self.text)
