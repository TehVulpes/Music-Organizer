from Tree import Tree
import os


class FileTree(Tree):
    def __init__(self, root, ignore_hidden=True):
        root = os.path.realpath(root)
        super().__init__(root)

        if os.path.isdir(root):
            for child in [file for file in os.listdir(root) if not file.startswith('.') or not ignore_hidden]:
                self.children += (FileTree(root + '/' + child),)
