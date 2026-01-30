from dom_utils import WIDTH, HEIGHT, HSTEP, VSTEP
from block_layout import BlockLayout

class DocumentLayout:
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.children = []
        self.x = None
        self.y = None
        self.width = None
        self.height = None

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        self.width = WIDTH - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP
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
