import skia

from blend import Blend
from dom_utils import dpx, paint_outline, paint_visual_effects
from draw_rrect import DrawRRect
from embed_layout import EmbedLayout
from transform import Transform

IFRAME_WIDTH_PX = 300
IFRAME_HEIGHT_PX = 150


class IframeLayout(EmbedLayout):
    def __init__(self, node, parent, previous, parent_frame) -> None:
        super().__init__(node, parent, previous, parent_frame)

    def layout(self):
        super().layout()

        width_attr = self.node.attributes.get("width")
        height_attr = self.node.attributes.get("height")

        zoom = self.zoom.read(notify=self.width)
        if width_attr:
            self.width.set(dpx(int(width_attr) + 2, zoom))
        else:
            self.width.set(dpx(IFRAME_WIDTH_PX + 2, zoom))

        zoom = self.zoom.read(notify=self.height)
        if height_attr:
            self.height.set(dpx(int(height_attr) + 2, zoom))
        else:
            self.height.set(dpx(IFRAME_HEIGHT_PX + 2, zoom))

        if self.node.frame and self.node.frame.loaded:
            self.node.frame.frame_height = self.height.get() - dpx(2, self.zoom.get())
            self.node.frame.frame_width = self.width.get() - dpx(2, self.zoom.get())

        height = self.height.read(notify=self.ascent)
        self.ascent.set(-height)
        self.descent.set(0)

    def paint(self):
        cmds = []

        rect = skia.Rect.MakeLTRB(
            self.x, self.y, self.x + self.width, self.y + self.height
        )
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            radius = dpx(
                float(self.node.style.get("border-radius", "0px")[:-2]), self.zoom
            )
            cmds.append(DrawRRect(rect, radius, bgcolor))
        return cmds

    def paint_effects(self, cmds):
        rect = skia.Rect.MakeLTRB(
            self.x, self.y, self.x + self.width, self.y + self.height
        )
        diff = dpx(1, self.zoom)
        scroll = (
            self.node.frame.scroll
            if (self.node.frame and self.node.frame.loaded)
            else 0
        )
        offset = (self.x + diff, self.y + diff - scroll)
        cmds = [Transform(offset, rect, self.node, cmds)]
        inner_rect = skia.Rect.MakeLTRB(
            self.x + diff,
            self.y + diff,
            self.x + self.width - diff,
            self.y + self.height - diff,
        )
        internal_cmds = cmds
        internal_cmds.append(
            Blend(1.0, "destination-in", [DrawRRect(inner_rect, 0, "white")], None)
        )
        cmds = [Blend(1.0, "source-over", internal_cmds, self.node)]
        paint_outline(self.node, cmds, rect, self.zoom)
        cmds = paint_visual_effects(self.node, cmds, rect)
        return cmds
