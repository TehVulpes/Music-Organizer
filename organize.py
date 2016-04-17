import os
import sys

import ID3
from FileTree import FileTree

root = '.'
audio_extensions = (
    'aac', 'm4a', 'm4b', 'm4p', 'm4v', 'm4r', '3gp', 'mp4',
    'aiff', 'aif', 'aifc',
    'ape', 'apl',
    'asf', 'wma', 'wmv',
    'flac',
    'mp3',
    'mp4',
    'mpc', 'mp+', 'mpp',
    'ogg', 'ogv', 'oga', 'ogx', 'ogm', 'spx', 'opus',
)
path_format = (
    ':albumartist:',
    ':year: - :album: [:FORMAT:]?label|catalogno?" {:label?:?label?"?catalogno?" "":catalogno?:}"',
    '?disctotal!1?"Disc :discnumber:"',
    ':tracknumber: :title:.:format:'
)


def parse_args(argv):
    global root

    for arg in argv[1:]:
        if not os.path.isdir(arg):
            raise Exception('"{}" is not a valid path'.format(arg))
        else:
            root = os.path.realpath(arg)


def print_layout(layout, depth=0):
    for key in layout.keys():
        print('    ' * depth + key)

        if type(layout[key]) == dict:
            print_layout(layout[key], depth + 1)


def main(argv):
    parse_args(argv)

    tree = FileTree(root)
    organized = {}

    for leaf in tree.file_iter():
        extension = os.path.splitext(leaf.value)[1][1:]

        if extension not in audio_extensions:
            continue

        layer = organized
        tags = ID3.get_tags(leaf.value)

        for string_format in path_format:
            path = ID3.format_string(string_format, tags, leaf.value)

            if path in layer:
                layer = layer[path]
            else:
                if string_format == path_format[-1]:
                    layer[path] = leaf
                else:
                    layer[path] = {}
                    layer = layer[path]

    print_layout(organized)


main(sys.argv)
