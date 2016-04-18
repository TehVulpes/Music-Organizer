class Tree:
    def __init__(self, value, parent=None):
        self.value = value
        self.children = ()
        self.parent = parent

    def is_leaf(self):
        return len(self.children) == 0

    def add_child(self, child):
        if isinstance(child, Tree):
            self.children += (child,)
        else:
            self.children += (Tree(child),)

    def has_child(self, value):
        for child in self.children:
            if child.value == value:
                return True

    def get_child(self, value):
        for child in self.children:
            if child.value == value:
                return child

        return None

    def depth_first_iter(self):
        yield self

        dirs = ()

        for child in self.children:
            if child.is_leaf():
                yield child
            else:
                dirs += (child,)

        for child in dirs:
            for element in child.depth_first_iter():
                yield element

    def __iadd__(self, other):
        self.add_child(other)

    def __str__(self):
        return '{} node: {}'.format(type(self).__name__, self.value.__str__())
