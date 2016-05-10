import sys
import time
import os
import stat
import re


class BashWriter:
    def __init__(self, root, dest, keep_formats, outfile=sys.stdout, errfile=sys.stderr):
        self.root = root
        self.dest = dest
        self.keep_formats = keep_formats
        self.outfile = outfile
        self.errfile = errfile

    def write_changes(self, id3_tree):
        self._write_header()
        self._write_body(id3_tree)

        if os.path.isfile(self.outfile.name):
            os.chmod(self.outfile.name, os.stat(self.outfile.name).st_mode | stat.S_IEXEC)

    def _write_header(self):
        self.output('#!/usr/bin/env bash')
        self.output('')
        self.output('COMMAND="{}"'.format(' '.join(sys.argv).replace('"', '').replace('\\', '')))
        self.output('SOURCE="{}"'.format(self.root))
        self.output('DESTINATION="{}"'.format(self.dest))
        self.output('DATE_CREATED="{}"'.format(time.strftime('%Y-%m-%d')))
        self.output('TIME_12HR="{}"'.format(time.strftime('%I:%M:%S %p')))
        self.output('TIME_24HR="{}"'.format(time.strftime('%H:%M:%S')))
        self.output('')
        permission_check = \
            '# Ensuring user really wants to migrate files\n' \
            'echo "This file is an automatic ID3-based Music organizer. It\'s potentially dangerous."\n' \
            'echo "It was generated on ${DATE_CREATED} (yyyy-mm-dd) at ${TIME_12HR} (${TIME_24HR})"\n' \
            'echo "The command used to generate it was ${COMMAND}"\n' \
            'echo ""\n' \
            'echo "This script will organize music from ${SOURCE} into ${DESTINATION}"\n' \
            'read -r -p "Are you sure you want to run this? [y/N] " response\n' \
            'case ${response} in\n' \
            '    [Yy][Ee][Ss]|[Yy])\n' \
            '        echo "Organizing music..."\n' \
            '        ;;\n' \
            '    *)\n' \
            '        echo "User didn\'t give permission; aborting"\n' \
            '        exit\n' \
            '        ;;\n' \
            'esac\n'
        self.output(permission_check)
        self.output('keep_files() {')
        for file_format in self.keep_formats:
            wildcard = '"${{1}}"/*.{}'.format(file_format)
            self.output('    if ls {} 1> /dev/null 2>&1; then cp {} "${{2}}"; fi'.format(wildcard, wildcard))
        self.output('}')
        self.output('')
        self.output('# Setting working directory to {}'.format(self.root.replace('$', '\\$')))
        self.output('cd "${SOURCE}"')

    def _write_body(self, id3_tree):
        created = []

        for item in id3_tree.leaf_iter():
            directory = item.parent.get_tree_path()

            if directory not in created:
                self.make_directories(created, directory)
                img_src = self.prepare_path('/'.join(item.value['src'].split('/')[:-1]))
                self.output('keep_files "{}" "{}"'.format(img_src, self.prepare_path(directory)))

            src = self.prepare_path(item.value['src'])
            dst = self.prepare_path(item.value['dst'])

            self.output('cp "{}" "{}"'.format(src, dst))

    def output(self, data, postfix='\n'):
        try:
            self.outfile.write(str(data + postfix))
        except TypeError:
            self.outfile.write(bytes(data + postfix, 'utf-8'))

    def prepare_path(self, string):
        return re.sub('//+', '/', self.rewrite_path_start(string.replace('$', '\\$'))).rstrip('/')

    def rewrite_path_start(self, path):
        check_order = [(self.root, '${SOURCE}/'), (self.dest, '${DESTINATION}/')]
        check_order.sort(key=lambda item: len(item[0]), reverse=True)

        if len(self.root) < len(self.dest):
            check_order = check_order[::-1]

        for check in check_order:
            if check[0] in path:
                path = check[1] + path[len(check[0]):]

        return path

    def make_directories(self, created, full_path):
        path = ''

        for part in full_path.split('/')[1:]:
            if len(part) == 0:
                continue

            path += '/' + part

            if path in created:
                continue
            else:
                created.append(path)
            if os.path.isdir(path):
                continue

            cleaned = self.prepare_path(path)

            self.output('\n# Creating directory for "{}"'.format(cleaned))
            self.output('mkdir "{}"'.format(cleaned))

        self.output('echo "Migrating to {}"'.format(self.prepare_path(full_path).replace('${DESTINATION}/', '')))
