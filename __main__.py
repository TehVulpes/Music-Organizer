#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect
import os
import sys

import ID3
import ID3Formatter
from FileTree import FileTree
from Tree import Tree
from BashWriter import BashWriter

root = '.'
dest = '../output'
path_format = (
    ':albumartist:',

    ':year: - :album: [:FORMAT:]' +
    '?label|catalogno?" {' +
    ':label?:?label?" "' +
    ':catalogno?:}"',

    '?disctotal!=1?"Disc :discnumber:"',
    ':tracknumber: :title:.:format:'
)
keep_formats = (
    'jpg', 'jpeg', 'jif', 'jfif', 'png', 'bmp', 'tiff', 'gif', 'pdf', 'txt'
)
outfile = sys.stdout
errfile = sys.stderr


def main(argv):
    parse_args(argv)

    file_tree = FileTree(root, add_children=True)
    id3_tree = get_id3_tree(file_tree)

    run_op(id3_tree)
    outfile.flush()
    outfile.close()


def get_id3_tree(file_tree):
    tree = Tree(os.path.abspath(dest))
    tree.value = tree.value[tree.value.rfind(os.path.sep) + 1:]
    rootlength = len(root) + 1

    for file in file_tree.file_iter():
        if file.get_extension() not in ID3.audio_extensions:
            continue

        level = tree
        tags = ID3.get_tags(file.value)

        for string_format in path_format:
            path = cleanup_path(ID3Formatter.format_string(string_format, tags, file.value))

            if len(path) == 0:
                continue

            child = level.get_child_tree(path)

            if child is None:
                if string_format == path_format[-1]:
                    level.add_child({
                        'name': path,
                        'src': file.value[rootlength:],
                        'dst': level.get_tree_path() + os.path.sep + path,
                        'tree': file
                    })
                else:
                    level.add_child(path)

            level = level.get_child_tree(path)

    return tree


def get_directory(tree, local=False):
    if tree.parent is None:
        return str(tree.value) if local else os.path.join(root, str(tree.value))
    else:
        postfix = tree.value['name'] if type(tree.value) == dict else str(tree.value)
        return os.path.join(get_directory(tree.parent, local), postfix)


def cleanup_path(path):
    replacements = {
        '\\': '-',
        '/': '-',
        ':': '-',
        '*': '•',
        '?': 'qt',
        '"': "'",
        '<': 'lt',
        '>': 'gt',
        '|': '-'
    }

    for symbol in replacements.keys():
        path = path.replace(symbol, replacements[symbol])

    return path


def print_layout(tree, depth=0):
    if type(tree.value) == dict:
        string = '"{}"  ->  "{}"'.format(tree.value['src'], tree.value['dst'])
        print(' ' * 4 * depth + string)
    else:
        print(' ' * 4 * depth + tree.value)

        for child in tree.children:
            print_layout(child, depth + 1)


def write_changes(tree):
    BashWriter(root, dest, keep_formats, outfile, errfile).write_changes(tree)


def parse_args(argv):
    global root
    global dest

    def print_mode():
        global run_op
        run_op = print_layout

    def write_mode():
        global run_op
        run_op = write_changes

    def set_outfile(filename):
        global outfile
        outfile = get_file(filename)

    def set_errfile(filename):
        global errfile
        errfile = get_file(filename)

    def set_destination(filename):
        global dest
        dest = os.path.abspath(filename)

    arg_logic = {
        'o': set_outfile,
        'e': set_errfile,
        'p': print_mode,
        's': write_mode,
        'd': set_destination
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


def get_file(filename):
    special = {
        'stdout': sys.stdout,
        'stderr': sys.stderr,
        'stdin': sys.stdin
    }

    if filename in special:
        return special[filename]
    else:
        return open(filename, 'wb')


run_op = write_changes

main(sys.argv)
