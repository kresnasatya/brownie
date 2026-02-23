class VisualEffect:
    def __init__(self, rect, children, node=None):
        self.rect = rect.makeOffset(0.0, 0.0)
        self.children = children
        self.node = node
        for child in children:
            self.rect.join(child.rect)
