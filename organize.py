import sys
import os
import mutagen
from FileTree import FileTree


root = '.'


def parse_args(argv):
    global root

    for arg in argv[1:]:
        if not os.path.isdir(arg):
            raise Exception('"{}" is not a valid path'.format(arg))
        else:
            root = os.path.realpath(arg)


def main(argv):
    parse_args(argv)

    tree = FileTree(root)

    for leaf in tree.file_iter():
        print(leaf.value)


main(sys.argv)
