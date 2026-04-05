from block_layout import BlockLayout
from dom_utils import HEIGHT, HSTEP, VSTEP, WIDTH, dpx
from protected_field import ProtectedField


class DocumentLayout:
    def __init__(self, node, frame=None):
        self.node = node
        self.frame = frame
        self.parent = None
        self.children = []

        self.x = ProtectedField()
        self.y = ProtectedField()
        self.width = ProtectedField()
        self.height = ProtectedField()
        self.zoom = ProtectedField()

    def layout(self, width, zoom):
        self.zoom.set(zoom)
        self.width.set(width - 2 * dpx(HSTEP, zoom))

        if not self.children:
            child = BlockLayout(self.node, self, None, self.frame)
        else:
            child = self.children[0]
        self.children = [child]
        child.zoom.mark()

        self.x.set(dpx(HSTEP, zoom))
        self.y.set(dpx(VSTEP, zoom))
        child.layout()
        self.height.copy(child.height)

    def should_paint(self):
        return True

    def paint(self):
        return []

    def __repr__(self):
        return "DocumentLayout()"

    def paint_effects(self, cmds):
        return cmds
