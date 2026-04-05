class ProtectedField:
    def __init__(self, obj, name) -> None:
        self.obj = obj
        self.name = name
        self.value = None
        self.dirty = True
        self.invalidations = set()

    def __repr__(self) -> str:
        return "ProtectedField({}, {})".format(
            self.obj.node if hasattr(self.obj, "node") else self.obj, self.name
        )

    def mark(self):
        if self.dirty:
            return
        self.dirty = True

    def get(self):
        assert not self.dirty
        return self.value

    def set(self, value):
        if value != self.value:
            self.notify()
        self.value = value
        self.dirty = False

    def notify(self):
        for field in self.invalidations:
            field.mark()

    def read(self, notify):
        self.invalidations.add(notify)
        return self.get()

    def copy(self, field):
        self.set(field.read(notify=self))
