class Tree:
    def __init__(self, value, parent=None):
        self.value = value
        self.children = ()
        self.parent = parent

    def is_leaf(self):
        return len(self.children) == 0

    def add_child(self, child):
        self.children += (self.get_tree(child),)

    def add_child_tree(self, children):
        if len(children) == 0:
            return

        if children[0] not in self:
            self.add_child(children[0])
        child = self.get_child_tree(children[0])

        child.add_child_tree(children[1:])

    def has_child(self, value):
        for child in self.children:
            if child.value == value:
                return True

        return False

    def get_child_tree(self, value):
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

    def leaf_iter(self):
        for item in self.depth_first_iter():
            if item.is_leaf():
                yield item

    def get_tree_path(self):
        path = self.value.__str__()

        if self.parent is not None:
            path = self.parent.get_tree_path() + '/' + path

        return path

    def get_tree(self, item):
        return item if isinstance(item, Tree) else Tree(item, parent=self)

    def __iadd__(self, other):
        self.add_child(other)

    def __contains__(self, item):
        return self.value == item or self.has_child(item)

    def __str__(self):
        return '{} node: {}'.format(type(self).__name__, self.value.__str__())
