import skia

from dom_utils import (
    dpx,
    font,
    get_font,
    linespace,
    paint_outline,
    paint_visual_effects,
)
from draw_text import DrawText
from protected_field import ProtectedField


class TextLayout:
    def __init__(self, node, word, parent, previous):
        self.node = node
        self.word = word
        self.children = []
        self.parent = parent
        self.previous = previous
        self.width = ProtectedField(self, "width", self.parent, [self.font])
        self.height = ProtectedField(self, "height", self.parent, [self.font])
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
        self.ascent = ProtectedField(self, "ascent", self.parent, [self.font])
        self.descent = ProtectedField(self, "descent", self.parent, [self.font])
        self.zoom = ProtectedField(self, "zoom", self.parent, [self.parent.zoom])
        if self.previous:
            x_dependencies = [self.previous.x, self.previous.font, self.previous.width]
        else:
            x_dependencies = [self.parent.x]
        self.x = ProtectedField(self, "x", self.parent, x_dependencies)
        self.y = ProtectedField(
            self, "y", self.parent, [self.ascent, self.parent.y, self.parent.ascent]
        )

    def layout(self):
        zoom = self.zoom.read(notify=self.font)
        self.font.set(font(self.node.style, zoom, notify=self.font))

        f = self.font.read(notify=self.width)
        self.width.set(f.measureText(self.word))

        if self.previous:
            prev_x = self.previous.x.read(notify=self.x)
            prev_font = self.previous.font.read(notify=self.x)
            prev_width = self.previous.width.read(notify=self.x)
            self.x.set(prev_x + prev_font.measureText(" ") + prev_width)
        else:
            self.x.copy(self.parent.x)

        f = self.font.read(notify=self.height)
        self.height.set(linespace(f) * 1.25)

        f = self.font.read(notify=self.ascent)
        self.ascent.set(f.getMetrics().fAscent * 1.25)
        self.descent.set(f.getMetrics().fDescent * 1.25)

    def paint(self):
        color = self.node.style["color"]
        return [DrawText(self.x, self.y, self.word, self.font, color)]

    def should_paint(self):
        return True

    def self_rect(self):
        return skia.Rect.MakeLTRB(
            self.x, self.y, self.x + self.width, self.y + self.height
        )

    def paint_effects(self, cmds):
        cmds = paint_visual_effects(self.node, cmds, self.self_rect())
        paint_outline(self.node, cmds, self.self_rect(), self.zoom)
        return cmds
