import ctypes
import sdl2
import skia
from visual_utils import parse_color

class DrawRect:
    def __init__(self, rect, color) -> None:
        self.rect = rect
        self.color = color

    def execute(self, canvas):
        paint = skia.Paint(
            Color=parse_color(self.color)
        )
        canvas.drawRect(self.rect, paint)
