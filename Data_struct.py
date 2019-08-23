import re
from y4mconv import yuvInfo


class Line:
    def __init__(self, input_url, codec_name, bit_depth, width, height, type, yuv_info):
        self.yuv_info = yuv_info
        self.input_url = input_url
        self.bit_depth = bit_depth
        self.width = width
        self.height = height
        self.type = type
        self.codec_name = codec_name
        self.output = []
        self.bit_rate = []
        self.fps = []
        self.psnr = []
        self.bd_psnr = None
        self.average_fps = None

    def parse_fps(self, line):
        if self.codec_name == 'x265':
            ss = re.findall(r'\(([\.0-9]*)[\r\n\t ]*fps\)', line[1])
            return float(ss[-1])
        elif self.codec_name == 'SVT':
            ss = re.findall(r'Average Speed:[\r\n\t ]*([\.0-9]*)[\r\n\t ]*fps', line[0])
            return float(ss[-1])
        elif self.codec_name == 'HM':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
            return float(ss[-1])

    def parse_bit_rate(self, line):
        if self.codec_name == 'x265':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]kb/s', line[1])
            return float(ss[-1])
        elif self.codec_name == 'svt':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
            return float(ss[-1])
        elif self.codec_name == 'HM':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
            return float(ss[-1])

    def check_info(self, line):
        if self.codec_name == 'x265':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]kb/s', line[1])
        elif self.codec_name == 'svt':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
        elif self.codec_name == 'HM':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
        return ss

    def add_info(self, line):
        self.bit_rate.append(self.parse_bit_rate(line))
        self.fps.append(self.parse_fps(line))

    def add_output(self, output):
        self.output.append(output)

    def add_psnr(self, psnr):
        self.psnr.append(psnr)

    def sort(self):
        print "do we really need sort?"

    def set_bd_psnr(self, bd_psnr):
        self.bd_psnr = bd_psnr

    def set_average_fps(self):
        self.average_fps = sum(self.fps) / len(self.fps)


class LineContain:
    def __init__(self, codec_num):
        self.baseline = None
        self.codec_num = codec_num
        self.group = {}
        self.group_tag = {}

    def set_baseline(self, line):
        self.baseline = line

    def build_group(self, codec):
        for encode in codec:
            self.group[encode[2]] = []
            self.group_tag[encode[2]] = 1

    def add_group_ele(self, codec_name, line):
        self.group[codec_name].append(line)

    def check_baseline(self, codec):
        codec_contain = [codec_name[2] for codec_name in codec]
        if 'HM' in codec_contain:
            self.set_baseline(self.group['HM'][0])
        else:
            self.set_baseline(self.group['svt'][0])

    def set_group_tag(self, codec_name):
        self.group_tag[codec_name] = 0


class CaseDate:
    def __init__(self):
        self.case = []

    def add_case(self, case):
        self.case.append(case)
