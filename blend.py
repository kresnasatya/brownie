import ctypes

import sdl2
import skia

from visual_effect import VisualEffect


def parse_blend_mode(blend_mode_str):
    if blend_mode_str == "multiply":
        return skia.BlendMode.kMultiply
    elif blend_mode_str == "difference":
        return skia.BlendMode.kDifference
    elif blend_mode_str == "destination-in":
        return skia.BlendMode.kDstIn
    elif blend_mode_str == "source-over":
        return skia.BlendMode.kSrcOver
    else:
        return skia.BlendMode.kSrcOver


class Blend(VisualEffect):
    def __init__(self, opacity, blend_mode, children, node):
        super().__init__(skia.Rect.MakeEmpty(), children, node)
        self.opacity = opacity
        self.blend_mode = blend_mode
        self.should_save = self.blend_mode or self.opacity < 1

        if self.should_save:
            self.needs_compositing = True

        self.children = children
        self.rect = skia.Rect.MakeEmpty()
        for cmd in self.children:
            self.rect.join(cmd.rect)

    def __repr__(self):
        args = ""
        if self.opacity < 1:
            args += ", opacity={}".format(self.opacity)
        if self.blend_mode:
            args += ", blend_mode={}".format(self.blend_mode)
        if not args:
            args = ", <no-op>"
        return "Blend({})".format(args[2:])

    def execute(self, canvas):
        paint = skia.Paint(
            Alphaf=self.opacity, BlendMode=parse_blend_mode(self.blend_mode)
        )
        if self.should_save:
            canvas.saveLayer(None, paint)
        for cmd in self.children:
            cmd.execute(canvas)
        if self.should_save:
            canvas.restore()

    def clone(self, child):
        return Blend(self.opacity, self.blend_mode, [child], self.node)
