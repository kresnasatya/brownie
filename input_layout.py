import ctypes
import sdl2
import skia
from dom_utils import get_font, linespace, paint_visual_effects
from draw_rrect import DrawRRect
from draw_text import DrawText
from draw_line import DrawLine
from text import Text

INPUT_WIDTH_PX = 200

class InputLayout:
    def __init__(self, node, parent, previous) -> None:
        self.node = node
        self.children = []
        self.parent = parent
        self.previous = previous
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.font = None

    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal":
            style = "roman"
        size = int(float(self.node.style["font-size"][:2]) * 0.75)
        self.font = get_font(size, weight, style)
        self.width = INPUT_WIDTH_PX
        if self.previous:
            space = self.previous.font.measureText(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x
        self.height = linespace(self.font)

    def should_paint(self):
        return True

    def paint(self):
        cmds = []
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            radius = float(self.node.style.get("border-radius", "0px")[:-2])
            cmds.append(DrawRRect(self.self_rect(), radius, bgcolor))
        text = ""
        if self.node.tag == "input":
            text = self.node.attributes.get("value", "")
        elif self.node.tag == "button":
            if len(self.node.children) == 1 and isinstance(self.node.children[0], Text):
                text = self.node.children[0].text
            else:
                print("Ignoring HTML contents inside button")
        color = self.node.style["color"]
        cmds.append(DrawText(self.x, self.y, text, self.font, color))

        if self.node.is_focused:
            cx = self.x + self.font.measureText(text)
            cmds.append(DrawLine(
                cx, self.y, cx, self.y + self.height, "black", 1
            ))
        return cmds

    def self_rect(self):
        return skia.Rect.MakeLTRB(
            l=self.x,
            t=self.y,
            r=self.x + self.width,
            b=self.y + self.height,
        )

    def paint_effects(self, cmds):
        return paint_visual_effects(self.node, cmds, self.self_rect())
