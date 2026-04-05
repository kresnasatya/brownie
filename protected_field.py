class ProtectedField:
    def __init__(self) -> None:
        self.value = None
        self.dirty = True

    def mark(self):
        if self.dirty:
            return
        self.dirty = True

    def get(self):
        assert not self.dirty
        return self.value

    def set(self, value):
        self.value = value
        self.dirty = False
