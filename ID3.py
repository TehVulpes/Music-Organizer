import os
import re
import sys

from mutagen import File as VorbisID3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError

album_tags = (
    'year', 'date', 'originalyear', 'originaldate', 'label', 'catalogno', 'upc', 'media', 'albumartist', 'disctotal',
    'discnumber'
)

album_tag_data = {}

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


def _format_year(year):
    return max(re.split('\\W', year[0]), key=len)


def _is_upc(string):
    return re.match('^\\d{12}$', string[0]) is not None


def _get_catalog_no(cat):
    for string in cat:
        if not _is_upc(cat):
            return string

    return cat[0]


def _get_upc(cat):
    for string in cat:
        if _is_upc(cat):
            return string

    return None


def _get_preslash(value, slash_required=False):
    return None if slash_required and '/' not in value[0] else value[0].split('/')[0]


def _get_postslash(value, slash_required=True):
    return None if slash_required and '/' not in value[0] else value[0].split('/')[-1]


def _delist(value):
    return value[0]


_tag_alias = (
    ('year', ('year', 'date', 'originalyear', 'originaldate'), _format_year),
    ('date', ('date', 'year', 'originaldate', 'originalyear'), _delist),
    ('originalyear', ('originalyear', 'originaldate', 'year', 'date'), _format_year),
    ('originaldate', ('originaldate', 'originalyear', 'date', 'year'), _delist),
    ('label', ('label', 'organization'), _delist),
    ('catalogno', ('catalognumber',), _get_catalog_no),
    ('upc', ('catalognumber',), _get_upc),
    ('media', ('media',), _delist),
    ('albumartist', ('albumartist', 'performer'), _delist),
    ('album', ('album',), _delist),
    ('genre', ('genre',), _delist),
    ('disctotal', ('totaldiscs', 'disctotal'), _delist),
    ('disctotal', ('discnumber',), _get_postslash),
    ('discnumber', ('discnumber',), _get_preslash),
    ('artist', ('artist', 'performer'), _delist),
    ('tracktotal', ('totaltracks',), _delist),
    ('tracktotal', ('tracknumber',), _get_postslash),
    ('tracknumber', ('tracknumber',), _get_preslash),
    ('title', ('title',), _delist)
)


def _request_tag_value(tags, tag, filename):
    if tag in album_tags:
        if tags['album'] is not None and tags['album'] in album_tag_data and tag in album_tag_data[tags['album']]:
            return album_tag_data[tags['album']][tag]

    sys.stdout.write('Enter value for tag "{}" in file "{}": '.format(tag, filename))
    sys.stdout.flush()
    value = sys.stdin.readline()

    if tag in album_tags and tags['album'] is not None:
        if tags['album'] not in album_tag_data:
            album_tag_data[tags['album']] = {}
        album_tag_data[tags['album']][tag] = value

    return value


def _conditional_split(string_format):
    error = Exception('Malformed conditional')

    if '?' not in string_format:
        return [string_format]

    parts = ['']
    level = 0
    in_tag = False

    for symbol in string_format:
        if symbol == ':':
            in_tag = not in_tag

        if in_tag:
            parts[-1] += symbol
            continue

        if level == 0:
            if symbol == '?':
                parts += ['']
                level += 1
            parts[-1] += symbol
        else:
            parts[-1] += symbol

            if level % 3 == 0:
                if symbol == '"':
                    level -= 3
                    if level == 0:
                        parts += ['']
                elif symbol == '?':
                    level += 1

            elif level % 3 == 1:
                if symbol == '"':
                    raise error
                elif symbol == '?':
                    level += 1

            elif level % 3 == 2:
                if symbol != '"':
                    raise error
                else:
                    level += 1

    if len(parts[0]) == 0:
        parts = parts[1:]

    if len(parts[-1]) == 0:
        parts = parts[:-1]

    return parts


def _test_condition(conditional, tags):
    conditional = conditional[1:conditional[1:].find('?') + 1]

    tests = {
        '!=': lambda tag, value: tag != value,
        '==': lambda tag, value: tag == value,
        '<>': lambda tag, value: tag != value,
        '>': lambda tag, value: tag > value,
        '>=': lambda tag, value: tag >= value,
        '<': lambda tag, value: tag < value,
        '<=': lambda tag, value: tag <= value
    }

    for condition in conditional.split('|'):
        met_requirements = True

        for test in tests.keys():
            if test in condition:
                expected_value = condition[condition.rfind(test) + len(test):]
                condition = condition[:condition.find(test)]

                if tags[condition] is None:
                    met_requirements = False
                    break

                if re.fullmatch('\\d*', expected_value) and re.fullmatch('\\d*', tags[condition]):
                    met_requirements = tests[test](int(tags[condition]), int(expected_value))
                else:
                    met_requirements = tests[test](tags[condition], expected_value)

                break

        if not met_requirements:
            continue

        return True

    return False


def pad_tag(tags, totaltag, paddedtag, filename):
    if tags[totaltag] is None:
        tags[totaltag] = _request_tag_value(tags, totaltag, filename)

    if len(tags[totaltag]) > 1:
        tags[paddedtag] = tags[paddedtag].zfill(len(tags[totaltag]))


def get_tags(filename):
    try:
        id3 = dict(EasyID3(filename))
    except ID3NoHeaderError:
        id3 = VorbisID3(filename)

    tags = {}

    for alias in _tag_alias:
        if alias[0] in tags and tags[alias[0]] is not None:
            continue

        for tag in alias[1]:
            if tag in id3:
                tags[alias[0]] = alias[2](id3[tag])
                break

        if alias[0] not in tags:
            tags[alias[0]] = None

    if tags['tracknumber'] is not None:
        pad_tag(tags, 'tracktotal', 'tracknumber', filename)
    if tags['discnumber'] is not None:
        pad_tag(tags, 'disctotal', 'discnumber', filename)

    tags['format'] = os.path.splitext(filename)[1][1:].lower()
    tags['FORMAT'] = os.path.splitext(filename)[1][1:].upper()

    return tags


def format_string(string_format, tags, filename):
    string = ''

    for section in _conditional_split(string_format):
        if section.startswith('?'):
            if _test_condition(section, tags):
                string += format_string(section[section.find('"') + 1:-1], tags, filename)
        else:
            for part in re.split('(:.*?:)*', section):
                if ':' in part:
                    part = part.replace(':', '')

                    required = '?' not in part
                    if not required:
                        part = part.replace('?', '')

                    if tags[part] is None:
                        if not required:
                            string = string.rstrip()
                            continue
                        else:
                            tags[part] = _request_tag_value(tags, part, filename)

                    string += tags[part]

                else:
                    string += part

    return string
