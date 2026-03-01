import skia

from paint_command import PaintCommand


class DrawImage(PaintCommand):
    def __init__(self, rect, image, quality):
        super().__init__(rect)
        self.image = image
        self.quality = parse_image_rendering(quality)

    def execute(self, canvas):
        canvas.drawImageRect(self.image, self.rect, self.quality)


def parse_image_rendering(quality):
    if quality == "high-quality":
        return skia.SamplingOptions(skia.CubicResampler.Mitchell())
    elif quality == "crisp-edges":
        return skia.SamplingOptions(skia.FilterMode.kNearest, skia.MipmapMode.kNone)
    else:
        return skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
