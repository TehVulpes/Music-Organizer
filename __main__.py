#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect
import os
import sys

import ID3
from BashWriter import BashWriter
from FileTree import FileTree
from ID3Tree import ID3Tree
from RuntimeOptions import RuntimeOptions

options = RuntimeOptions()


def main(argv):
    parse_args(argv)

    file_tree = FileTree(options.root, add_children=True)
    id3_tree = ID3Tree(
        options.dest, '/'.join(options.path_format),
        [file.value for file in file_tree.file_iter() if os.path.splitext(file.value)[-1][1:] in ID3.audio_extensions]
    )

    run_op(id3_tree)
    options.outfile.flush()
    options.outfile.close()


def print_layout(tree, depth=0):
    if type(tree.value) == dict:
        string = '"{}"  ->  "{}"'.format(tree.value['src'], tree.value['dst'])
        print(' ' * 4 * depth + string)
    else:
        print(' ' * 4 * depth + tree.value)

        for child in tree.children:
            print_layout(child, depth + 1)


def write_changes(tree):
    BashWriter(options.root, options.dest, options.keep_formats, options.outfile, options.errfile).write_changes(tree)


def parse_args(argv):
    def print_mode():
        options.run_op = print_layout

    def write_mode():
        options.run_op = write_changes

    def set_outfile(filename):
        options.outfile = get_file(filename)

    def set_errfile(filename):
        options.errfile = get_file(filename)

    def set_destination(filename):
        options.dest = os.path.abspath(filename)

    def set_format(path_format):
        options.path_format = path_format.split('/')

    arg_logic = {
        'p': print_mode,
        's': write_mode,
        'o': set_outfile,
        'e': set_errfile,
        'd': set_destination,
        'f': set_format
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

            options.root = os.path.realpath(arg)


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
