import sys
import time
import os
import stat


class BashWriter:
    def __init__(self, root, dest, keep_formats, outfile=sys.stdout, errfile=sys.stderr):
        self.root = root
        self.dest = dest
        self.keep_formats = keep_formats
        self.outfile = outfile
        self.errfile = errfile

    def write_changes(self, tree):
        self._write_header()

        created = ()

        for item in tree.depth_first_iter():
            if not item.is_leaf():
                directory = item.get_tree_path()

                if directory not in created and not os.path.isdir(directory):
                    self.output('\n# Creating directory for "{}"'.format(self.clean(directory)))

                    self.output('mkdir "${{DESTINATION}}/{}"'.format(
                        self.clean('/'.join(item.get_tree_path().split('/')[1:]))
                    ))

                    self.output('echo "Migrating to {}"'.format(directory))

                    created += (directory,)
            else:
                self.output('cp "${{SOURCE}}/{}" "${{DESTINATION}}/{}"'.format(
                    self.clean(item.value['src']), '/'.join(self.clean(item.value['dst']).split('/')[1:])
                ))

        self.output('\n\n# Moving special formats to new location')
        self.output('echo "Migrating files with the following extensions: {}"'.format(str(self.keep_formats)))

        created = ()

        for item in [item for item in tree.depth_first_iter() if item.is_leaf()]:
            src = item.value['tree'].value[:item.value['tree'].value.rfind(os.path.sep)]
            dst = os.path.abspath(self.dest[:self.dest.rfind(os.path.sep)] + '/' +
                                  item.value['dst'][:item.value['dst'].rfind(os.path.sep)])

            if dst in created:
                continue
            created += (dst,)

            self.output('keep_files "{}" "{}"'.format(self.clean(src), self.clean(dst)))

        if os.path.isfile(self.outfile.name):
            try:
                os.chmod(self.outfile.name, os.stat(self.outfile.name).st_mode | stat.S_IEXEC)
            except Exception:
                pass

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
        self.output('# Setting working directory to {}'.format(self.clean(self.root)))
        self.output('cd "${SOURCE}"')

    def output(self, data, postfix='\n'):
        try:
            self.outfile.write(str(data + postfix))
        except TypeError:
            self.outfile.write(bytes(data + postfix, 'utf-8'))

    def clean(self, string):
        string = string.replace('$', '\\$')

        return string
