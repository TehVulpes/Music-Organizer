import re

import ID3

_replacements = {
    '$': '\\$',
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


def format_path(string_format, tags, filename):
    return format_string(string_format, {key: _clean(value) for key, value in tags.items()}, filename)


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
                            tags[part] = ID3.request_tag_value(tags, part, filename)

                    string += tags[part]

                else:
                    string += part

    return string


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
        '<>': lambda tag, value: tag != value,
        '==': lambda tag, value: tag == value,
        '>': lambda tag, value: tag > value,
        '>=': lambda tag, value: tag >= value,
        '<': lambda tag, value: tag < value,
        '<=': lambda tag, value: tag <= value
    }

    for condition in conditional.split('|'):
        met_requirements = False

        if condition in tags and tags[condition] is not None:
            return True

        for test in tests.keys():
            if test not in condition:
                continue

            expected_value = condition[condition.rfind(test) + len(test):]
            condition = condition[:condition.find(test)]

            if tags[condition] is None or len(tags[condition]) == 0:
                continue

            if re.fullmatch('\\d+', expected_value) and re.fullmatch('\\d+', tags[condition]):
                met_requirements = tests[test](int(tags[condition]), int(expected_value))
            else:
                met_requirements = tests[test](tags[condition], expected_value)

            break

        if met_requirements:
            return True

    return False


def _clean(string):
    if string is None:
        return None

    for key in _replacements.keys():
        string = string.replace(key, _replacements[key])

    return string
