from block_layout import BlockLayout
from dom_utils import HEIGHT, HSTEP, VSTEP, WIDTH, dpx


class DocumentLayout:
    def __init__(self, node, frame=None):
        self.node = node
        self.frame = frame
        self.parent = None
        self.children = []
        self.x = None
        self.y = None
        self.width = None
        self.height = None

    def layout(self, width, zoom):
        self.zoom = zoom
        if not self.children:
            child = BlockLayout(self.node, self, None, self.frame)
        else:
            child = self.children[0]
        self.children = [child]

        self.width = width - 2 * dpx(HSTEP, self.zoom)
        self.x = dpx(HSTEP, self.zoom)
        self.y = dpx(VSTEP, self.zoom)
        child.layout()
        self.height = child.height

    def should_paint(self):
        return True

    def paint(self):
        return []

    def __repr__(self):
        return "DocumentLayout()"

    def paint_effects(self, cmds):
        return cmds
