import ctypes

import sdl2
import skia

from dom_utils import dpx, linespace, paint_outline, paint_visual_effects
from draw_line import DrawCursor, DrawLine
from draw_rrect import DrawRRect
from draw_text import DrawText
from embed_layout import EmbedLayout
from text import Text

INPUT_WIDTH_PX = 200


class InputLayout(EmbedLayout):
    def __init__(self, node, parent, previous, frame) -> None:
        super().__init__(node, parent, previous, frame)

    def layout(self):
        if not self.layout_needed():
            return

        EmbedLayout.layout(self)

        zoom = self.zoom.read(notify=self.width)
        self.width.set(dpx(INPUT_WIDTH_PX, zoom))

        font = self.font.read(notify=self.height)
        self.height.set(linespace(font))

        height = self.height.read(notify=self.ascent)
        self.ascent.set(-height)
        self.descent.set(0)

    def paint(self):
        cmds = []
        bgcolor = self.node.style["background-color"].get()
        if bgcolor != "transparent":
            radius = float(self.node.style["border-radius"].get()[:-2])
            cmds.append(DrawRRect(self.self_rect(), radius, bgcolor))
        text = ""
        if self.node.tag == "input":
            text = self.node.attributes.get("value", "")
        elif self.node.tag == "button":
            if len(self.node.children) == 1 and isinstance(self.node.children[0], Text):
                text = self.node.children[0].text
            else:
                print("Ignoring HTML contents inside button")
        color = self.node.style["color"].get()
        cmds.append(DrawText(self.x.get(), self.y.get(), text, self.font.get(), color))

        if self.node.is_focused and self.node.tag == "input":
            cmds.append(DrawCursor(self, self.font.get().measureText(text)))
        return cmds

    def self_rect(self):
        return skia.Rect.MakeLTRB(
            l=self.x.get(),
            t=self.y.get(),
            r=self.x.get() + self.width.get(),
            b=self.y.get() + self.height.get(),
        )

    def paint_effects(self, cmds):
        cmds = paint_visual_effects(self.node, cmds, self.self_rect())
        paint_outline(self.node, cmds, self.self_rect(), self.zoom)
        return cmds
