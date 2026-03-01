import skia

from dom_utils import dpx, get_font, linespace, paint_outline, paint_visual_effects
from draw_text import DrawText


class TextLayout:
    def __init__(self, node, word, parent, previous):
        self.node = node
        self.word = word
        self.children = []
        self.parent = parent
        self.previous = previous
        self.x = None
        self.y = None
        self.width = None
        self.height = None

    def layout(self):
        self.zoom = self.parent.zoom
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal":
            style = "roman"
        px_size = float(self.node.style["font-size"][:2])
        size = dpx(px_size * 0.75, self.zoom)
        self.font = get_font(size, weight, style)
        self.width = self.font.measureText(self.word)
        if self.previous:
            space = self.previous.font.measureText(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x
        self.height = linespace(self.font)

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
