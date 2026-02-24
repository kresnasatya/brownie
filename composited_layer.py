import ctypes

import skia

from draw_outline import DrawOutline

SHOW_COMPOSITED_LAYER_BORDERS = True


class CompositedLayer:
    def __init__(self, skia_context, display_item):
        self.skia_context = skia_context
        self.surface = None
        self.display_items = [display_item]

    def composited_bounds(self):
        rect = skia.Rect.MakeEmpty()
        for item in self.display_items:
            rect.join(item.rect)
        rect.outset(1, 1)
        return rect

    def raster(self):
        bounds = self.composited_bounds()
        if bounds.isEmpty():
            return
        irect = bounds.roundOut()

        if not self.surface:
            self.surface = skia.Surface.MakeRenderTarget(
                self.skia_context,
                skia.Budgeted.kNo,
                skia.ImageInfo.MakeN32Premul(irect.width(), irect.height()),
            )
            assert self.surface
        canvas = self.surface.getCanvas()

        canvas.clear(skia.ColorTRANSPARENT)
        canvas.save()
        canvas.translate(-bounds.left(), -bounds.top())
        for item in self.display_items:
            item.execute(canvas)
        canvas.restore()

        if SHOW_COMPOSITED_LAYER_BORDERS:
            border_rect = skia.Rect.MakeXYWH(
                1, 1, irect.width() - 2, irect.height() - 2
            )
            DrawOutline(border_rect, "red", 1).execute(canvas)

    def add(self, display_item):
        self.display_items.append(display_item)

    def can_merge(self, display_item):
        return display_item.parent == self.display_items[0].parent
