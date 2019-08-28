import sys
import re

def create_output_filename(input_filename):
    return re.sub(r'\..*$', '.gutenberg.html', input_filename)

def is_header(line):
    return re.compile(r'^#{1,6} ').search(line) is not None

def is_blank(line):
    return re.compile(r'^(\n|\r)$').search(line) is not None

def is_preformatted(line):
    return re.compile(r'^\t| {4}').search(line) is not None

def is_list_item(line):
    return re.compile(r'^- ').search(line) is not None

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
    return re.sub(r'[_\*]{1}(\w*\s?\w*)[_\*]{1}', r'<em>\g<1></em>', line)

def convert_inline_strong(line):
    return re.sub(r'\*{2}(\w*\s?\w*)\*{2}', r'<strong>\g<1></strong>', line)

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
    return re.sub(r'^- (.*)', r'<li>\g<1></li>', line)

def get_list_beginning():
    return '<!-- wp:list -->\n<ul>\n';

def get_list_end():
    return '</ul>\n<!-- /wp:list -->\n'

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
                    output_lines.append(get_list_beginning())

                output_lines.append(convert_to_list_item(line))
            else:
                if is_list_item(previous_line):
                    output_lines.append(get_list_end())

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
