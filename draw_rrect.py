import ctypes
import sdl2
import skia
from visual_utils import parse_color
from paint_command import PaintCommand

class DrawRRect(PaintCommand):
    def __init__(self, rect, radius, color):
        super().__init__(rect)
        self.rrect = skia.RRect.MakeRectXY(rect, radius, radius)
        self.color = color

    def __repr__(self):
        return "DrawRRect(rect={}, color={})".format(
            str(self.rrect),
            self.color
        )

    def execute(self, canvas):
        paint = skia.Paint(
            Color=parse_color(self.color),
        )
        canvas.drawRRect(self.rrect, paint)
