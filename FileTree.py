import os

from Tree import Tree


class FileTree(Tree):
    def __init__(self, root, parent=None, ignore_hidden=True):
        if not os.path.exists(root):
            raise Exception('"{}" does not exist'.format(root))

        root = os.path.realpath(root)
        super().__init__(root, parent)

        if os.path.isdir(root):
            for child in [file for file in os.listdir(root) if not file.startswith('.') or not ignore_hidden]:
                self.add_child(FileTree(root + '/' + child, parent=self))

    def is_dir(self):
        return os.path.isdir(self.value)

    def is_file(self):
        return os.path.isfile(self.value)

    def file_iter(self):
        for child in super().depth_first_iter():
            if child.is_file():
                yield child
