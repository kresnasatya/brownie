import ctypes
import sdl2
import skia
from visual_utils import parse_color
from paint_command import PaintCommand

class DrawRect(PaintCommand):
    def __init__(self, rect, color) -> None:
        super().__init__(rect)
        self.rect = rect # I don't know why I must declare this.
        self.color = color

    def __repr__(self):
        return("DrawRect(top={} left={} " +
            "bottom={} right={} color={}"
        ).format(
            self.top, self.left, self.bottom,
            self.right, self.color
        )

    def execute(self, canvas):
        paint = skia.Paint(
            Color=parse_color(self.color)
        )
        canvas.drawRect(self.rect, paint)
