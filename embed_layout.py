from dom_utils import font
from protected_field import ProtectedField


class EmbedLayout:
    def __init__(self, node, parent, previous, frame) -> None:
        self.node = node
        self.frame = frame
        node.layout_object = self
        self.children = []
        self.width = ProtectedField(self, "width", self.parent, [self.zoom])
        self.height = ProtectedField(
            self, "height", self.parent, [self.zoom, self.font, self.width]
        )
        self.ascent = ProtectedField(self, "ascent", self.parent, [self.height])
        self.descent = ProtectedField(self, "descent", self.parent, [])
        self.font = ProtectedField(
            self,
            "font",
            self.parent,
            [
                self.zoom,
                self.node.style["font-weight"],
                self.node.style["font-style"],
                self.node.style["font-size"],
            ],
        )
        self.zoom = ProtectedField(self, "zoom", self.parent, [self.parent.zoom])
        self.parent = parent
        self.previous = previous
        if self.previous:
            x_dependencies = [self.previous.x, self.previous.font, self.previous.width]
        else:
            x_dependencies = [self.parent.x]
        self.x = ProtectedField(self, "x", self.parent, x_dependencies)
        self.y = ProtectedField(
            self, "y", self.parent, [self.ascent, self.parent.y, self.parent.ascent]
        )

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
