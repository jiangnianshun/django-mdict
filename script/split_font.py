from fontTools.ttLib import TTFont
import sys
from fontTools.subset import main as subset


def ttf2xml(ttf_file):
    xml_file = ttf_file[:ttf_file.rfind('.')] + '.xml'
    font = TTFont(ttf_file)
    font.saveXML(xml_file)


def extract_font(font_file, code_start, code_end, output_file):
    unicode = '--unicodes=U+' + str(code_start) + '-' + str(code_end)
    output_file = '--output-file=' + output_file
    sys.argv = [None, font_file, unicode, output_file]
    subset()


def dec2hex(dec):
    return str(hex(dec))


def get_median(data_list):
    data_list.sort()
    list_length = len(data_list)
    return data_list[int(list_length / 2)]


def get_max(data_list):
    data_list.sort()
    return data_list[-1]


def split_ttf(ttf_file):
    font = TTFont(ttf_file)
    cmap = font['cmap'].getBestCmap()
    code_list = list(cmap.keys())

    median_code = get_median(code_list)
    max_code = get_max(code_list)

    code0 = '0000'
    code1 = dec2hex(median_code)[2:]
    code2 = dec2hex(max_code)[2:]

    dot_mark = ttf_file.rfind('.')
    output_file1 = ttf_file[:dot_mark] + '-1.ttf'
    output_file2 = ttf_file[:dot_mark] + '-2.ttf'
    extract_font(ttf_file, code0, code1, output_file1)
    extract_font(ttf_file, code1, code2, output_file2)
    print(ttf_file, code0, code1, code2)


if __name__ == '__main__':
    # 对大小超过30MB的全宋体字体文件进行拆分
    split_ttf('FSung-2.ttf')
    split_ttf('FSung-F.ttf')
