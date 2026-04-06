import skia

from dom_utils import dpx, linespace
from draw_image import DrawImage
from embed_layout import EmbedLayout


class ImageLayout(EmbedLayout):
    def __init__(self, node, parent, previous, frame) -> None:
        super().__init__(node, parent, previous, frame)

    def layout(self):
        if not self.layout_needed():
            return
        EmbedLayout.layout(self)
        # self.width = dpx(self.node.image.width(), self.zoom)
        # self.img_height = dpx(self.node.image.height(), self.zoom)
        # self.height = max(self.img_height, linespace(self.font))
        # self.ascent = -self.height
        # self.descent = 0
        width_attr = self.node.attributes.get("width")
        height_attr = self.node.attributes.get("height")
        image_width = self.node.image.width()
        image_height = self.node.image.height()

        aspect_ratio = image_width / image_height

        w_zoom = self.zoom.read(notify=self.width)
        h_zoom = self.zoom.read(notify=self.height)
        if width_attr and height_attr:
            self.width.set(dpx(int(width_attr), w_zoom))
            self.img_height = dpx(int(height_attr), h_zoom)
        elif width_attr:
            self.width.set(dpx(int(width_attr), w_zoom))
            w = self.width.read(notify=self.height)
            self.img_height = w / aspect_ratio
        elif height_attr:
            self.img_height = dpx(int(height_attr), h_zoom)
            self.width.set(self.img_height * aspect_ratio)
        else:
            self.width.set(dpx(image_width, w_zoom))
            self.img_height = dpx(image_height, h_zoom)

        font = self.font.read(notify=self.height)
        self.height.set(max(self.img_height, linespace(font)))

        height = self.height.read(notify=self.ascent)
        self.ascent.set(-height)
        self.descent.set(0)

    def paint(self):
        cmds = []
        rect = skia.Rect.MakeLTRB(
            self.x.get(),
            self.y.get() + self.height.get() - self.img_height,
            self.x.get() + self.width.get(),
            self.y.get() + self.height.get(),
        )
        quality = self.node.style["image-rendering"].get()
        cmds.append(DrawImage(rect, self.node.image, quality))
        return cmds

    def paint_effects(self, cmds):
        return cmds
