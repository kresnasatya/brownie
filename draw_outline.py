import ctypes
import sdl2
import skia
from visual_utils import parse_color
from paint_command import PaintCommand

class DrawOutline(PaintCommand):
    def __init__(self, rect, color, thickness):
        super().__init__(rect)
        self.color = color
        self.thickness = thickness

    def execute(self, canvas):
        paint = skia.Paint(
            Color=parse_color(self.color),
            StrokeWidth=self.thickness,
            Style=skia.Paint.kStroke_Style,
        )
        canvas.drawRect(self.rect, paint)
