import sys
import re
from enum import Enum

class Mode(Enum):
    PARAGRAPH = 1
    ORDERED_LIST = 2
    PREFORMATTED = 3
    LIST = 4
    HEADING = 5

class Tag(Enum):
    CODE = 1
    EM = 2
    STRONG = 3

def create_output_filename(input_filename):
    return re.sub(r'\..*$', '.gutenberg.html', input_filename)

def is_header(line):
    return re.compile(r'^#{1,6} ').search(line) is not None

def is_blank(line):
    return re.compile(r'^(\n|\r)$').search(line) is not None

def is_preformatted(line):
    return re.compile(r'^\t| {4}').search(line) is not None

def is_list_item(line):
    return re.compile(r'^(-|\d+\.) ').search(line) is not None

def get_list_mode(line):
    return Mode.LIST if re.compile(r'^- ').search(line) else Mode.ORDERED_LIST

def convert_to_header(line):
    level = len(re.findall(r'#', line))
    text = parse_line(re.sub(r'^#{1,6} |\n$', '', line))
    heading = '{"level":' + str(level) + '} ' if level > 2 else ''

    return '<!-- wp:heading {heading}-->\n' \
        '<h{level}>{text}</h{level}>\n' \
        '<!-- /wp:heading -->\n'.format(level=level, text=text, heading=heading)

def convert_to_paragraph(line):
    return '<!-- wp:paragraph -->\n' \
        '<p>{line}</p>\n' \
        '<!-- /wp:paragraph -->\n'.format(
        line=parse_line(re.sub(r'\n$', '', line))
    )

def convert_to_list_item(line):
    return parse_line(re.sub(r'^(-|\d+\.) (.*)', r'<li>\g<2></li>', line))

def get_list_beginning(ordered=False):
    return '<!-- wp:list {description}-->\n<{type}>\n'.format(
        description = r'{"ordered":true} ' if ordered else '',
        type = 'ol' if ordered else 'ul'
    )

def get_list_end(ordered=False):
    return '</{type}>\n<!-- /wp:list -->\n'.format(
        type = 'ol' if ordered else 'ul'
    )

def convert_to_preformatted(line):
    return re.sub(r'^\t| {4}', '', line, 1)

def get_preformatted_beginning(code=False):
    return '<!-- wp:{preformatted} -->\n' \
        '<pre class="wp-block-{preformatted}">\n'.format(
            preformatted='code' if code else 'preformatted'
        )

def get_preformatted_end(code=False):
    return '</pre>\n' \
        '<!-- /wp:{preformatted} -->\n'.format(
            preformatted='code' if code else 'preformatted'
        )

def main(argv):
    if len(argv) == 0:
        print("Missing input_filename argument")
        return None

    input_filename = argv[0]
    output_filename = argv[1] if len(argv) > 1 else create_output_filename(argv[0])

    output_lines = []
    mode_stack = []

    with open(input_filename, 'r') as file:
        previous_line = None

        for line in file.readlines():
            if is_header(line):
                output_lines.append(convert_to_header(line))
            elif is_preformatted(line):
                if is_blank(previous_line) or is_header(previous_line):
                    mode_stack.append(Mode.PREFORMATTED)
                    output_lines.append(get_preformatted_beginning(False))

                output_lines.append(convert_to_preformatted(line))
            elif is_list_item(line):
                if not is_list_item(previous_line):
                    mode = get_list_mode(line)
                    mode_stack.append(mode)
                    output_lines.append(get_list_beginning(mode is Mode.ORDERED_LIST))

                output_lines.append(convert_to_list_item(line))
            elif get_last(mode_stack) is Mode.ORDERED_LIST:
                output_lines.append(get_list_end(True))
                mode_stack.pop()

            elif get_last(mode_stack) is Mode.LIST:
                output_lines.append(get_list_end())
                mode_stack.pop()

            elif get_last(mode_stack) is Mode.PREFORMATTED:
                output_lines.append(get_preformatted_end(False))
                mode_stack.pop()

            else:
                if not is_blank(line):
                    output_lines.append(convert_to_paragraph(line))

            previous_line = line

        file.close()

    with open(output_filename, 'w') as file:
        file.writelines(output_lines)
        file.close()

    print(input_filename, output_filename)

def parse_line(line):
    tag_stack = []
    line_stack = []
    previous_char = None

    for char in line:
        if char == '`':
            if get_last(tag_stack) is Tag.CODE:
                # End of CODE
                line_stack.append('</code>')
                tag_stack.pop()
            else:
                # Start of CODE
                line_stack.append('<code>')
                tag_stack.append(Tag.CODE)

        elif get_last(tag_stack) is Tag.CODE:
            line_stack.append(char)

        elif char == '*' and previous_char == '*':
            if is_tag_type(line_stack[-1], Tag.EM):
                if get_last(tag_stack) is Tag.EM:
                    tag_stack.pop()

                line_stack.pop()

            if get_last(tag_stack) is Tag.STRONG:
                # End of STRONG
                line_stack.append('</strong>')
                tag_stack.pop()
            else:
                # Start of STRONG
                line_stack.append('<strong>')
                tag_stack.append(Tag.STRONG)

        elif char == '*':
            if get_last(tag_stack) is Tag.EM:
                # End of EM
                line_stack.append('</em>')
                tag_stack.pop()
            else:
                # Start of EM
                line_stack.append('<em>')
                tag_stack.append(Tag.EM)

        else:
            line_stack.append(char)

        previous_char = char

    return ''.join(line_stack)

def is_tag_type(string, tag_type):
    return re.compile(get_tag_pattern(tag_type)).search(string) is not None

def get_tag_pattern(tag_type):
    if tag_type == Tag.STRONG:
        return r'^</?strong>$'

    if tag_type == Tag.EM:
        return r'^</?em>$'

    if tag_type == Tag.CODE:
        return r'^</?code>'

def get_last(array):
    if len(array) > 0:
        return array[-1]

    return None

if __name__ == '__main__':
    main(sys.argv[1:])
