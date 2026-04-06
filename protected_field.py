class ProtectedField:
    def __init__(self, obj, name, parent=None, dependencies=None) -> None:
        self.obj = obj
        self.name = name
        self.value = None
        self.dirty = True
        self.invalidations = set()
        self.parent = parent
        self.frozen_dependencies = dependencies != None
        if dependencies != None:
            for dependency in dependencies:
                dependency.invalidations.add(self)

    def __repr__(self) -> str:
        return "ProtectedField({}, {})".format(
            self.obj.node if hasattr(self.obj, "node") else self.obj, self.name
        )

    def mark(self):
        if self.dirty:
            return
        self.dirty = True
        self.set_ancestor_dirty_flags()

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
        if notify.frozen_dependencies:
            assert notify in self.invalidations
        else:
            self.invalidations.add(notify)
        return self.get()

    def copy(self, field):
        self.set(field.read(notify=self))

    def set_ancestor_dirty_flags(self):
        parent = self.parent
        while parent and not parent.has_dirty_descendants:
            parent.has_dirty_descendants = True
            parent = parent.parent

    def set_dependencies(self, dependencies):
        for dependency in dependencies:
            dependency.invalidations.add(self)
        self.frozen_dependencies = True
