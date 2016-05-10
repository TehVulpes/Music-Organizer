import re

import ID3
import ID3Formatter
from Tree import Tree


class ID3Tree(Tree):
    def __init__(self, destination, path_format, filenames):
        super().__init__(destination)

        for filename in filenames:
            child_tree = re.sub('//+', '/',
                                ID3Formatter.format_path(path_format, ID3.get_tags(filename), filename)).split('/')
            child_tree[-1] = {
                'name': child_tree[-1],
                'src': filename,
                'dst': '{}/{}'.format(destination, '/'.join(child_tree))
            }

            super().add_child_tree(child_tree)
