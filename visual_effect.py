class VisualEffect:
    def __init__(self, rect, children):
        self.rect = rect.makeOffset(0.0, 0.0)
        self.children = children
        for child in children:
            self.rect.join(child.rect)
