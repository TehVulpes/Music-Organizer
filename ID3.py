import os
import re
import sys

from mutagen import File as VorbisID3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError

album_tags = (
    'year', 'date', 'originalyear', 'originaldate', 'label', 'catalogno', 'upc', 'media', 'albumartist', 'disctotal',
    'tracktotal'
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

    return None


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


def request_tag_value(tags, tag, filename):
    if tag in album_tags:
        if tags['album'] is not None and tags['album'] in album_tag_data and tag in album_tag_data[tags['album']]:
            return album_tag_data[tags['album']][tag]

    sys.stdout.write('Enter value for tag "{}" in file "{}": '.format(tag, filename))
    sys.stdout.flush()
    value = sys.stdin.readline().replace('\n', '')

    if tag in album_tags and tags['album'] is not None:
        if tags['album'] not in album_tag_data:
            album_tag_data[tags['album']] = {}
        album_tag_data[tags['album']][tag] = value

    return value


def pad_tag(tags, totaltag, paddedtag, filename):
    if tags[totaltag] is None:
        tags[totaltag] = request_tag_value(tags, totaltag, filename)

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
    tags.update({key.upper(): value.upper() if value is not None else None for key, value in tags.items()})

    return tags
