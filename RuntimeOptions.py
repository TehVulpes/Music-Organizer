import sys


class RuntimeOptions:
    def __init__(self):
        self.root = '.'
        self.dest = '../output'
        self.path_format = (
            ':albumartist:',

            ':year: - :album: [:FORMAT:]' +
            '?label|catalogno?" {' +
            ':label?:?label?" "' +
            ':catalogno?:}"',

            '?disctotal!=1?"Disc :discnumber:"',
            ':tracknumber: :title:.:format:'
        )
        self.keep_formats = (
            'jpg', 'jpeg', 'jif', 'jfif', 'png', 'bmp', 'tiff', 'gif', 'pdf', 'txt'
        )
        self.outfile = sys.stdout
        self.errfile = sys.stderr
