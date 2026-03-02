from dom_utils import font


class EmbedLayout:
    def __init__(self, node, parent, previous) -> None:
        self.node = node
        self.children = []
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.font = None
        self.parent = parent
        self.previous = previous

    def layout(self):
        self.zoom = self.parent.zoom
        self.font = font(self.node.style, self.zoom)
        if self.previous:
            space = self.previous.font.measureText(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

    def should_paint(self):
        return True
