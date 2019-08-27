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

def convert_to_header(line):
    level = len(re.findall(r'#', line))
    text = re.sub(r'^#{1,6} |\n$', '', line)

    return '<!-- wp:header -->\n' \
        '<h{level}>{text}</h{level}>\n' \
        '<!-- /wp:header -->\n'.format(level=level, text=text)

def convert_inline_code(line):
    return re.sub(r'`(\S+)`', r'<code>\g<1></code>', line)

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

def convert_to_preformatted(line):
    return re.sub(r'^\t| {4}', '', line, 1)

def get_preformatted_beginning(code=False):
    return '<!-- wp:{preformatted} -->\n' \
        '<pre>{code}\n'.format(
            code='<code>' if code else '',
            preformatted='code' if code else 'preformatted'
        )

def get_preformatted_end(code=False):
    return '{code}</pre>\n' \
        '<!-- /wp:{preformatted} -->\n'.format(
            code='</code>' if code else '',
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
                    output_lines.append(get_preformatted_beginning(True))
                    output_lines.append(convert_to_preformatted(line))
                else:
                    output_lines.append(convert_to_preformatted(line))
            elif is_blank(line) and is_preformatted(previous_line):
                output_lines.append(get_preformatted_end(True))
            elif is_blank(previous_line) or is_header(previous_line) and not is_blank(line):
                output_lines.append(convert_to_paragraph(line))
            # else:
            #     print(line)

            previous_line = line

        file.close()

    with open(output_filename, 'w') as file:
        file.writelines(output_lines)
        file.close()

    print(input_filename, output_filename)

if __name__ == '__main__':
    main(sys.argv[1:])
