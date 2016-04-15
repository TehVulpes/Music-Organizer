class Tree:
    def __init__(self, value):
        self.value = value
        self.children = ()

    def is_leaf(self):
        return len(self.children) == 0

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
