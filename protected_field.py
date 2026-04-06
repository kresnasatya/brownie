from constants import CSS_PROPERTIES


class ProtectedField:
    def __init__(
        self, obj, name, parent=None, dependencies=None, invalidations=None
    ) -> None:
        self.obj = obj
        self.name = name
        self.parent = parent

        self.value = None
        self.dirty = True
        self.invalidations = set()
        self.frozen_dependencies = dependencies != None
        if dependencies != None:
            for dependency in dependencies:
                dependency.invalidations.add(self)
        else:
            assert (
                self.name in ["height", "ascent", "descent", "children"]
                or self.name in CSS_PROPERTIES
            )
        self.frozen_invalidations = invalidations != None
        if invalidations != None:
            assert self.name == "children"
            for invalidation in invalidations:
                self.invalidations.add(invalidation)

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
        self.set_ancestor_dirty_flags()

    def read(self, notify):
        if notify.frozen_dependencies or self.frozen_invalidations:
            assert notify in self.invalidations
        else:
            self.invalidations.add(notify)

        # This section should add PRINT_INVALIDATION_DEPENDENCIES: https://github.com/browserengineering/book/blob/ae18040e30bc4aff1dfb477314dc6355c21d027c/src/lab16.py#L122
        # It's good for debugging. But, I don't know how to do it in proper way.

        return self.get()

    def copy(self, field):
        self.set(field.read(notify=self))

    def set_ancestor_dirty_flags(self):
        parent = self.parent
        while parent and not parent.has_dirty_descendants:
            parent.has_dirty_descendants = True
            parent = parent.parent

    def set_dependencies(self, dependencies):
        assert (
            self.name in ["height", "ascent", "descent"] or self.name in CSS_PROPERTIES
        )
        assert self.name == "height" or not self.frozen_dependencies
        for dependency in dependencies:
            dependency.invalidations.add(self)
        self.frozen_dependencies = True
