from dom_utils import font
from protected_field import ProtectedField


class EmbedLayout:
    def __init__(self, node, parent, previous, frame) -> None:
        self.node = node
        self.frame = frame
        node.layout_object = self
        self.children = []
        self.x = ProtectedField()
        self.y = ProtectedField()
        self.width = ProtectedField()
        self.height = ProtectedField()
        self.font = ProtectedField()
        self.zoom = ProtectedField()
        self.parent = parent
        self.previous = previous

    def layout(self):
        self.zoom.copy(self.parent.zoom)

        zoom = self.zoom.read(notify=self.font)
        self.font = font(self.node.style, zoom)
        if self.previous:
            space = self.previous.font.measureText(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

    def should_paint(self):
        return True
