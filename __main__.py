import inspect
import os
import sys

import ID3
from Tree import Tree
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

    ':year: - :album: [:FORMAT:]' +
    '?label|catalogno|media?" {' +
    ':media?:?media?" "' +
    ':label?:?label?" "' +
    ':catalogno?:}"',

    '?disctotal!1?"Disc :discnumber:"',
    ':tracknumber: :title:.:format:'
)
outfile = sys.stdout


def main(argv):
    parse_args(argv)

    tree = FileTree(root, add_children=True)
    organized = get_id3_tree(tree)

    print_layout(organized)
    outfile.flush()
    outfile.close()


def get_id3_tree(file_tree):
    tree = Tree('output')

    for file in file_tree.file_iter():
        if file.extension() not in ID3.audio_extensions:
            continue

        level = tree
        tags = ID3.get_tags(file.value)

        for string_format in path_format:
            path = ID3.format_string(string_format, tags, file.value)

            if len(path) == 0:
                continue

            child = level.get_child(path)

            if child is None:
                if string_format == path_format[-1]:
                    level.add_child({'src': file.value, 'dst': path, 'tree': file})
                else:
                    level.add_child(path)

            level = level.get_child(path)

    return tree


def print_layout(tree, depth=0):
    if type(tree.value) == dict:
        string = '"{}"  ->  "{}"'.format(tree.value['src'], tree.value['dst'])
        output(' ' * 4 * depth + string)
    else:
        output(' ' * 4 * depth + tree.value)

        for child in tree.children:
            print_layout(child, depth + 1)


def output(data, postfix='\n'):
    outfile.write(data + postfix)


def parse_args(argv):
    global root

    arg_logic = {
        'o': set_outfile
    }

    i = 1
    while i < len(argv):
        arg = argv[i]
        i += 1

        if arg[0] == '-':
            for symbol in arg[1:]:
                if symbol not in arg_logic:
                    raise Exception('"{}" is not a recognized argument'.format(symbol))

                logic = arg_logic[symbol]

                arg_count = len(inspect.signature(logic).parameters)

                if i + arg_count > len(argv):
                    raise Exception('"{}" requires more arguments than {}'.format(symbol, argv[i:]))

                args = argv[i:i + arg_count]
                logic(*args)

                i += arg_count
        else:
            if not os.path.exists(arg):
                raise Exception('"{}" is not a valid path'.format(arg))

            root = os.path.realpath(arg)


def set_outfile(filename):
    global outfile

    special = {
        'stdout': sys.stdout,
        'stderr': sys.stderr
    }

    if filename in special:
        outfile = special[filename]
    else:
        outfile = open(filename, 'w')


main(sys.argv)
