import sys
import re
from enum import Enum

class Mode(Enum):
    PARAGRAPH = 1
    ORDERED_LIST = 2
    PREFORMATTED = 3
    LIST = 4
    HEADING = 5

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
    text = re.sub(r'^#{1,6} |\n$', '', line)
    heading = '{"level":' + str(level) + '} ' if level > 2 else ''

    return '<!-- wp:heading {heading}-->\n' \
        '<h{level}>{text}</h{level}>\n' \
        '<!-- /wp:heading -->\n'.format(level=level, text=text, heading=heading)

def convert_inline_code(line):
    return re.sub(r'`(\S* *\S*)`', r'<code>\g<1></code>', line)

def convert_inline_italic(line):
    return re.sub(r'[_\*]{1}(\b.*\b)[_\*]{1}', r'<em>\g<1></em>', line)

def convert_inline_strong(line):
    return re.sub(r'\*{2}(\b.*\b)\*{2}', r'<strong>\g<1></strong>', line)

def convert_to_paragraph(line):
    return '<!-- wp:paragraph -->\n' \
        '<p>{line}</p>\n' \
        '<!-- /wp:paragraph -->\n'.format(
        line=convert_inline_code(
            convert_inline_italic(
                convert_inline_strong(re.sub(r'\n$', '', line))
            )
        )
    )

def convert_to_list_item(line):
    return re.sub(r'^(-|\d+\.) (.*)', r'<li>\g<2></li>', line)

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
                    output_lines.append(get_preformatted_beginning(False))

                output_lines.append(convert_to_preformatted(line))
            elif is_list_item(line):
                if not is_list_item(previous_line):
                    mode = get_list_mode(line)
                    mode_stack.append(mode)
                    output_lines.append(get_list_beginning(mode is Mode.ORDERED_LIST))

                output_lines.append(convert_to_list_item(line))
            elif len(mode_stack) > 0:
                if mode_stack[-1] is Mode.ORDERED_LIST:
                    output_lines.append(get_list_end(True))

                if mode_stack[-1] is Mode.LIST:
                    output_lines.append(get_list_end())

                mode_stack.pop()
            else:
                if is_preformatted(previous_line):
                    output_lines.append(get_preformatted_end(False))

                if not is_blank(line):
                    output_lines.append(convert_to_paragraph(line))

            previous_line = line

        file.close()

    with open(output_filename, 'w') as file:
        file.writelines(output_lines)
        file.close()

    print(input_filename, output_filename)

if __name__ == '__main__':
    main(sys.argv[1:])
