#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect
import time
import os
import stat
import sys

import ID3
from FileTree import FileTree
from Tree import Tree

root = '.'
dest = '../output'
path_format = (
    ':albumartist:',

    ':year: - :album: [:FORMAT:]' +
    '?label|catalogno|media?" {' +
    ':media?:?media?" "' +
    ':label?:?label?" "' +
    ':catalogno?:}"',

    '?disctotal!=1?"Disc :discnumber:"',
    ':tracknumber: :title:.:format:'
)
keep_formats = (
    'jpg', 'jpeg', 'jif', 'jfif', 'png', 'bmp', 'tiff', 'gif', 'pdf'
)
outfile = sys.stdout
errfile = sys.stderr


def main(argv):
    parse_args(argv)

    tree = FileTree(root, add_children=True)
    organized = get_id3_tree(tree)

    run_op(organized)
    outfile.flush()
    outfile.close()


def get_id3_tree(file_tree):
    tree = Tree(dest)
    rootlength = len(root) + 1

    for file in file_tree.file_iter():
        if file.extension() not in ID3.audio_extensions:
            continue

        level = tree
        tags = ID3.get_tags(file.value)

        for string_format in path_format:
            path = cleanup_path(ID3.format_string(string_format, tags, file.value))

            if len(path) == 0:
                continue

            child = level.get_child(path)

            if child is None:
                if string_format == path_format[-1]:
                    level.add_child({
                        'name': path,
                        'src': file.value[rootlength:],
                        'dst': os.path.join(get_directory(level, local=True), path),
                        'tree': file
                    })
                else:
                    level.add_child(path)

            level = level.get_child(path)

    return tree


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
        output(' ' * 4 * depth + string)
    else:
        output(' ' * 4 * depth + tree.value)

        for child in tree.children:
            print_layout(child, depth + 1)


def write_changes(tree):
    output('#!/usr/bin/env bash')

    output('# Ensuring user really wants to migrate files')
    output('echo "This file is an automatic ID3-based Music organizer. It\'s potentially dangerous."')
    output('echo "It was generated on {} (yyyy-mm-dd) at {} ({})"'.format(
        time.strftime('%Y-%m-%d'), time.strftime('%I:%M:%S %p'), time.strftime('%H:%M:%S')
    ))
    output('echo "The command used to generate it was {}"'.format(
        ' '.join(sys.argv).replace('"', '').replace('\\', ''))
    )
    output('echo ""')
    output('echo "This script will organize music from {} into {}"'.format(root, os.path.realpath(root + '/' + dest)))

    output('read -r -p "Are you sure you want to run this? [y/N] " response')
    output('case $response in')
    output('    [Yy][Ee][Ss]|[Yy])')
    output('        echo "Organizing music..."')
    output('        ;;')
    output('    *)')
    output('        echo "User didn\'t provide permission; aborting"')
    output('        exit')
    output('        ;;')
    output('esac')

    output('# Setting working directory to {}'.format(root))
    output('cd {}'.format(root))

    created = ()

    for item in tree.depth_first_iter():
        directory = get_directory(item, local=True)

        if not item.is_leaf():
            if directory not in created and not os.path.isdir(directory):
                output('\n# Creating directory for "{}"'.format(directory))
                output('mkdir "{}"'.format(directory))
                output('echo Migrating to "{}"'.format(directory))

                created += (directory,)
        else:
            output('cp "{}" "{}"'.format(item.value['src'], item.value['dst']))

    output('\n\n# Moving special formats to new location')
    output('echo "Migrating files with the following extensions: {}"'.format(str(keep_formats)))

    extra_copied = ()

    for item in [item for item in tree.depth_first_iter() if item.is_leaf()]:
        if item.parent in extra_copied:
            continue

        extra_copied += (item.parent,)

        src = item.value['tree'].parent.value[len(root) + 1:]
        dst = get_directory(item, local=True)
        dst = dst[:dst.rfind('/')]

        for keep_format in keep_formats:
            keep_wildcard = '"{}/"*".{}"'.format(src, keep_format)
            output('if ls {} 1> /dev/null 2>&1; then cp {} "{}"; fi'.format(keep_wildcard, keep_wildcard, dst))

    if os.path.isfile(outfile.name):
        try:
            os.chmod(outfile.name, os.stat(outfile.name).st_mode | stat.S_IEXEC)
        except Exception:
            pass


def get_directory(tree, local=False):
    if tree.parent is None:
        return str(tree.value) if local else os.path.join(root, str(tree.value))
    else:
        postfix = tree.value['name'] if type(tree.value) == dict else str(tree.value)
        return os.path.join(get_directory(tree.parent, local), postfix)


def output(data, postfix='\n'):
    outfile.write((data + postfix).encode('utf-8'))


def parse_args(argv):
    global root

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

    arg_logic = {
        'o': set_outfile,
        'e': set_errfile,
        'p': print_mode,
        's': write_mode
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
