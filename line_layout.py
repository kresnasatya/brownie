import skia

from dom_utils import paint_outline
from protected_field import ProtectedField
from text_layout import TextLayout


class LineLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        self.width = ProtectedField()
        self.y = ProtectedField()
        self.x = ProtectedField()
        self.ascent = ProtectedField()
        self.descent = ProtectedField()

    def layout(self):
        self.zoom = self.parent.zoom
        self.width.copy(self.parent.width)
        self.x.copy(self.parent.x)

        if self.previous:
            prev_y = self.previous.y.read(notify=self.y)
            prev_height = self.previous.height.read(notify=self.y)
            self.y.set(prev_y + prev_height)
        else:
            self.y.copy(self.parent.y)

        for word in self.children:
            word.layout()

        if not self.children:
            self.ascent.set(0)
            self.descent.set(0)
            self.height.set(0)
            return

        self.ascent.set(
            max([-child.ascent.read(notify=self.ascent) for child in self.children])
        )
        self.descent.set(
            max([child.descent.read(notify=self.descent) for child in self.children])
        )

        for child in self.children:
            new_y = self.y.read(notify=child.y)
            new_y += self.ascent.read(notify=child.y)
            new_y += child.ascent.read(notify=child.y)
            if isinstance(child, TextLayout):
                new_y += child.ascent.read(notify=child.y) / 1.25
            else:
                new_y += child.ascent.read(notify=child.y)
            child.y.set(new_y)

        max_ascent = self.ascent.read(notify=self.ascent)
        max_descent = self.ascent.read(notify=self.descent)
        self.height.set(max_ascent + max_descent)

    def paint(self):
        return []

    def should_paint(self):
        return True

    def paint_effects(self, cmds):
        outline_rect = skia.Rect.MakeEmpty()
        outline_node = None
        for child in self.children:
            if child.node.parent.is_focused:
                outline_rect.join(child.self_rect())
                outline_node = child.node.parent
        if outline_node:
            paint_outline(outline_node, cmds, outline_rect, self.zoom)
        return cmds
