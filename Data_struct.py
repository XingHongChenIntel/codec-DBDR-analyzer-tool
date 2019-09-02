import re
import csv
import subprocess
from ycbcr import YCbCr
import bjontegaard_metric as BD


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
        self.psnr_luam_chro = []
        self.bd_psnr = None
        self.average_fps = None
        self.bd_rate = None
        self.qp = []
        self.ref = None
        self.instance_name = None

    def check_blank(self, ss):
        if len(ss):
            return ss[-1]
        else:
            return 0

    def parse_fps(self, line):
        if self.codec_name == 'x265':
            ss = re.findall(r'\(([\.0-9]*)[\r\n\t ]*fps\)', line[1])
            return float(self.check_blank(ss))
        elif self.codec_name == 'svt':
            ss = re.findall(r'Average Speed:[\r\n\t ]*([\.0-9]*)[\r\n\t ]*fps', line[0])
            return float(self.check_blank(ss))
        elif self.codec_name == 'HM':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
            return float(self.check_blank(ss))
        else:
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]*fps', line[0])
            return float(self.check_blank(ss))

    def parse_bit_rate(self, line):
        if self.codec_name == 'x265':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]kb/s', line[1])
            return float(self.check_blank(ss))
        elif self.codec_name == 'svt':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
            return float(self.check_blank(ss))
        elif self.codec_name == 'HM':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
            return float(self.check_blank(ss))
        else:
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
            return float(self.check_blank(ss))

    def check_info(self, line):
        if self.codec_name == 'x265':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]kb/s', line[1])
        elif self.codec_name == 'svt':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
        elif self.codec_name == 'HM':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
        else:
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
        return ss

    def add_info(self, line, codec):
        self.bit_rate.append(self.parse_bit_rate(line))
        self.fps.append(self.parse_fps(line))
        self.ref = codec[3]
        self.instance_name = codec[4]

    def add_output(self, output):
        self.output.append(output)

    def add_psnr(self, psnr):
        self.psnr.append(psnr)

    def add_lucha_psnr(self, psnr):
        self.psnr_luam_chro.append(psnr)

    def add_qp(self, qp):
        self.qp.append(qp)

    def sort(self):
        print("bit_rate info:", self.bd_psnr, self.psnr_luam_chro, self.bit_rate)

    def set_bd_psnr(self, bd_psnr):
        self.bd_psnr = bd_psnr

    def set_average_fps(self):
        self.average_fps = sum(self.fps) / len(self.fps)

    def get_psnr(self, line):
        input_url = line.input_url[0]
        output = line.output
        width = line.width
        height = line.height
        pipe_contain = []
        for out in output:
            arg = 'ffmpeg -s %sx%s -i %s -s %sx%s -i %s -lavfi psnr="stats_file=psnr.log" -f null -' % \
                  (width, height, input_url, width, height, out)
            p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pipe_contain.append(p)
        for p in pipe_contain:
            info = p.communicate()
            psnr = re.findall(r'average:[\r\n\t ]*([\.0-9]*)', info[1])
            line.add_lucha_psnr(float(self.check_blank(psnr)))
        line.set_average_fps()
        line.set_bd_psnr(BD.BD_PSNR_Average(line.bit_rate, line.psnr_luam_chro))
        line.sort()


class LineContain:
    def __init__(self, codec_num):
        self.baseline = None
        self.codec_num = codec_num
        self.group = {}
        self.group_tag = {}
        self.group_bdrate = {}
        self.yuv_info = None

    def set_data_type(self, yuv_info):
        self.yuv_info = yuv_info

    def set_baseline(self, line):
        self.baseline = line

    def build_group(self, codec):
        for encode in codec:
            self.group[encode[2] + '_' + encode[4]] = []
            self.group_bdrate[encode[2] + '_' + encode[4]] = []
            self.group_tag[encode[2] + '_' + encode[4]] = 1

    def add_group_ele(self, codec_name, line):
        self.group[codec_name].append(line)

    def check_baseline(self, codec):
        codec_contain = [codec_name[2] for codec_name in codec]
        instance_contain = [instance_name[4] for instance_name in codec]
        if 'HM' in codec_contain:
            self.set_baseline(self.group['HM_' + instance_contain[codec_contain.index('HM')]][0])
        elif 'svt' in codec_contain:
            self.set_baseline(self.group['svt_' + instance_contain[codec_contain.index('svt')]][0])
        else:
            print "there is no baseline encode"
            for i in self.group:
                self.set_baseline(self.group[i][0])
                break

    def set_group_tag(self, codec_name):
        self.group_tag[codec_name] = 0

    def get_psnr(self, line):
        yuv = YCbCr(filename=line.input_url, filename_diff=line.output, width=int(line.width),
                    height=int(line.height), yuv_format_in=line.type, bitdepth=int(line.bit_depth))
        for infile in range(len(line.input_url)):
            for diff_file in range(len(line.output)):
                psnr_frame = [p for p in yuv.psnr_all(diff_file, infile)]
                line.add_psnr(psnr_frame[-1])
                line.add_lucha_psnr(psnr_frame[-1][-1])
            line.sort()
            line.set_average_fps()
            line.set_bd_psnr(BD.BD_PSNR_Average(line.bit_rate, line.psnr_luam_chro))

    def get_bd_rate(self, baseline, line):
        return BD.BD_RATE(baseline.bit_rate, baseline.psnr_luam_chro, line.bit_rate, line.psnr_luam_chro)

    def calculate_psnr(self):
        for pool in self.group.values():
            for line in pool:
                self.get_psnr(line)

    def calculate_bd_rate(self):
        for pool in self.group.values():
            for line in pool:
                bd_rate = self.get_bd_rate(self.baseline, line)
                line.bd_rate = bd_rate
                self.group_bdrate[line.codec_name + '_' + line.instance_name].append(bd_rate)

    def calculate(self):
        # self.calculate_psnr()
        self.calculate_bd_rate()


class CaseDate:
    def __init__(self, path):
        self.case = []
        self.case_group = {'360': [], '480': [], '720': [], '1080': [],
                           '1152': [], '2304': [], '3840': [], }
        self.case_num = None
        self.datafile = None
        self.path = path

    def add_case(self, case, yuv_info):
        self.case.append(case)
        if yuv_info.height in self.case_group:
            self.case_group[yuv_info.height].append(case)
        else:
            self.case_group[yuv_info.height] = []
            self.case_group[yuv_info.height].append(case)

    def set_case_num(self):
        self.case_num = len(self.case)

    def write_pool_info(self, line_pool, file_line):
        mode = 0
        for encode in line_pool.group.values():
            for line in encode:
                for i in range(len(line.output)):
                    file_line[0] = line.yuv_info.yuv_name
                    file_line[1] = line.height + 'p'
                    file_line[2] = line.codec_name + '_' + line.instance_name
                    file_line[3] = mode
                    file_line[4] = line.qp[i]
                    file_line[5] = line.psnr_luam_chro[i]
                    file_line[6] = line.bit_rate[i]
                    file_line[7] = line.fps[i]
                    file_line[8] = line.bd_rate
                    file_line[9] = line.bd_psnr
                    yield file_line
            mode += 1

    def setup_file(self):
        header = ['yuv name', 'type', 'encode', 'mode', 'qp', 'psnr', 'bit_rate', 'fps', 'BD_rate', 'Bd_psnr']
        file_contain = []
        with open(self.path, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for pic in self.case:
                for p in self.write_pool_info(pic, header):
                    print p
                    file_contain.append(p)
            for l in file_contain:
                writer.writerow(l)
