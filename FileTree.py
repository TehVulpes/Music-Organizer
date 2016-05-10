import os

from Tree import Tree


class FileTree(Tree):
    def __init__(self, root, parent=None, ignore_hidden=True, add_children=False):
        if not os.path.exists(root):
            raise Exception('"{}" does not exist'.format(root))

        root = os.path.realpath(root)
        super().__init__(root, parent)

        if add_children and self.is_dir():
            for child in self.enumerate_children(ignore_hidden):
                self.add_child(FileTree(root + '/' + child, self, ignore_hidden, add_children))

    def enumerate_children(self, ignore_hidden=True):
        return [file for file in os.listdir(self.value) if not file.startswith('.') or not ignore_hidden]

    def is_dir(self):
        return os.path.isdir(self.value)

    def is_file(self):
        return os.path.isfile(self.value)

    def file_iter(self):
        for child in self.depth_first_iter():
            if child.is_file():
                yield child
