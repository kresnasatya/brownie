import skia

from blend import Blend
from dom_utils import dpx, paint_outline, paint_visual_effects
from draw_rrect import DrawRRect
from embed_layout import EmbedLayout
from transform import Transform
from visual_effect import VisualEffect

IFRAME_WIDTH_PX = 300
IFRAME_HEIGHT_PX = 150


class IframeLayout(EmbedLayout):
    def __init__(self, node, parent, previous, parent_frame) -> None:
        super().__init__(node, parent, previous, parent_frame)

    def layout(self):
        if not self.layout_needed():
            return
        EmbedLayout.layout(self)

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
            self.node.frame.document.width.mark()

        height = self.height.read(notify=self.ascent)
        self.ascent.set(-height)
        self.descent.set(0)

    def paint(self):
        cmds = []

        rect = skia.Rect.MakeLTRB(
            self.x.get(),
            self.y.get(),
            self.x.get() + self.width.get(),
            self.y.get() + self.height.get(),
        )
        bgcolor = self.node.style["background-color"].get()
        if bgcolor != "transparent":
            radius = dpx(
                float(self.node.style.get("border-radius", "0px")[:-2]), self.zoom
            )
            cmds.append(DrawRRect(rect, radius, bgcolor))
        return cmds

    def paint_effects(self, cmds):
        rect = skia.Rect.MakeLTRB(
            self.x.get(),
            self.y.get(),
            self.x.get() + self.width.get(),
            self.y.get() + self.height.get(),
        )
        diff = dpx(1, self.zoom.get())
        offset = (self.x.get() + diff, self.y.get() + diff)
        cmds: list[VisualEffect] = []
        cmds.append(Transform(offset, rect, self.node, cmds))
        inner_rect = skia.Rect.MakeLTRB(
            self.x.get() + diff,
            self.y.get() + diff,
            self.x.get() + self.width.get() - diff,
            self.y.get() + self.height.get() - diff,
        )
        internal_cmds: list[VisualEffect] = cmds
        internal_cmds.append(
            Blend(1.0, "destination-in", [DrawRRect(inner_rect, 0, "white")], None)
        )
        cmds = [Blend(1.0, "source-over", internal_cmds, self.node)]
        paint_outline(self.node, cmds, rect, self.zoom.get())
        cmds = paint_visual_effects(self.node, cmds, rect)
        return cmds
