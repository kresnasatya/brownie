import skia

from dom_utils import dpx, linespace
from draw_image import DrawImage
from embed_layout import EmbedLayout


class ImageLayout(EmbedLayout):
    def __init__(self, node, parent, previous) -> None:
        super().__init__(node, parent, previous)

    def layout(self):
        super().layout()
        self.width = dpx(self.node.image.width(), self.zoom)
        self.img_height = dpx(self.node.image.height(), self.zoom)
        self.height = max(self.img_height, linespace(self.font))
        self.ascent = -self.height
        self.descent = 0

    def paint(self):
        cmds = []
        rect = skia.Rect.MakeLTRB(
            self.x,
            self.y + self.height - self.img_height,
            self.x + self.width,
            self.y + self.height,
        )
        quality = self.node.style.get("image-rendering", "auto")
        cmds.append(DrawImage(self.node.image, rect, quality))
        return cmds
