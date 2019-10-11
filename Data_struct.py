import os
import re
import csv
import subprocess
import time
from ycbcr import YCbCr
import bjontegaard_metric as BD
from multiprocessing import Process, Value, Array


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
        self.psnr_luam = []
        self.psnr_charm_cb = []
        self.psnr_charm_cr = []
        self.bd_psnr = None
        self.BD_psnr = None
        self.BD_psnr_luam = None
        self.BD_psnr_charm_cb = None
        self.BD_psnr_charm_cr = None
        self.average_fps = None
        self.bd_rate = None
        self.bd_rate_luma = None
        self.bd_rate_charm_cb = None
        self.bd_rate_charm_cr = None
        self.qp = []
        self.ref = None
        self.instance_name = None

    def check_blank(self, ss):
        if len(ss):
            return ss[-1]
        else:
            return 0

    def parse_fps(self, line):
        if self.codec_name == 'x265' or self.codec_name == 'x264':
            ss = re.findall(r'\(([\.0-9]*)[\r\n\t ]*fps\)', line[1])
            return float(self.check_blank(ss))
        elif self.codec_name == 'svt':
            ss = re.findall(r'Average Speed:[\r\n\t ]*([\.0-9]*)[\r\n\t ]*fps', line[0])
            return float(self.check_blank(ss))
        elif self.codec_name == 'HM':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]*kbps', line[0])
            return float(self.check_blank(ss))
        else:
            if len(line[0]) is 0:
                ss = re.findall(r'([\.0-9]*)[\r\n\t ]*fps', line[1])
                return float(self.check_blank(ss))
            else:
                ss = re.findall(r'([\.0-9]*)[\r\n\t ]*fps', line[0])
                return float(self.check_blank(ss))

    def parse_bit_rate(self, line):
        if self.codec_name == 'x265' or self.codec_name == 'x264':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]*kb/s', line[1])
            return float(self.check_blank(ss))
        elif self.codec_name == 'svt':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]*kbps', line[0])
            return float(self.check_blank(ss))
        elif self.codec_name == 'HM':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]*kbps', line[0])
            return float(self.check_blank(ss))
        elif self.codec_name == 'AV1':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]*b/s', line[1])
            return float(self.check_blank(ss)) / 1000
        else:
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]*kbps', line[0])
            return float(self.check_blank(ss))

    def check_info(self, line):
        if self.codec_name == 'x265' or self.codec_name == 'x264':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]*kb/s', line[1])
        elif self.codec_name == 'svt':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]*kbps', line[0])
        elif self.codec_name == 'HM':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]*kbps', line[0])
        elif self.codec_name == 'AV1':
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]*b/s', line[1])
        else:
            ss = re.findall(r'([\.0-9]*)[\r\n\t ]*kbps', line[0])
        return ss

    def add_info(self, line, codec):
        # self.bit_rate.append(self.parse_bit_rate(line))
        self.fps.append(self.parse_fps(line))
        self.ref = codec[3]
        self.instance_name = codec[4]

    def calculate_frame(self, line):
        frame_size = (int(line.width) * int(line.height) * 3 / 2)
        if line.bit_depth == '8':
            bitsize = 1
        else:
            bitsize = 2
        num_frame = (os.path.getsize(line.input_url[0]) / frame_size) / bitsize
        return num_frame

    def add_bitrate(self, line, benchmark):
        frame = self.calculate_frame(line)
        bitrate = os.path.getsize(benchmark) * 8 / (float(frame / 60) * 1000)
        self.bit_rate.append(bitrate)

    def add_output(self, output):
        self.output.append(output)

    def add_psnr(self, psnr):
        self.psnr.append(psnr)

    def add_lucha_psnr(self, psnr):
        self.psnr_luam.append(psnr)

    def add_qp(self, qp):
        self.qp.append(qp)

    def sort(self):
        print("bit_rate info:", self.psnr, self.psnr_luam, self.bit_rate)

    def set_bd_psnr(self, bd_psnr):
        self.bd_psnr = bd_psnr

    def set_average_fps(self):
        self.average_fps = sum(self.fps) / len(self.fps)

    def get_psnr_ffmpeg(self, line):
        input_url = line.input_url[0]
        output = line.output
        width = line.width
        height = line.height
        pipe_contain = []
        time_b = time.time()
        for out in output:
            arg = 'ffmpeg -s %sx%s -i %s -s %sx%s -i %s -lavfi psnr="stats_file=psnr.log" -f null -' % \
                  (width, height, input_url, width, height, out)
            p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pipe_contain.append(p)
        for p in pipe_contain:
            info = p.communicate()
            psnr = re.findall(r'average:[\r\n\t ]*([\.0-9]*)', info[1])
            line.add_lucha_psnr(float(self.check_blank(psnr)))
        elapsed = (time.time() - time_b)
        m, s = divmod(elapsed, 60)
        h, m = divmod(m, 60)
        print("calculate psnr time used : %d:%02d:%02d" % (h, m, s))
        line.set_average_fps()
        line.set_bd_psnr(BD.BD_PSNR_Average(line.bit_rate, line.psnr_luam_chro))
        line.sort()

    def get_psnr(self, line):
        yuv = YCbCr(filename=line.input_url, filename_diff=line.output, width=int(line.width),
                    height=int(line.height), yuv_format_in=line.type, bitdepth=int(line.bit_depth))
        time_b = time.time()
        for infile in range(len(line.input_url)):
            p_pool = []
            for diff_file in range(len(line.output)):
                psnr = yuv.psnr_all(diff_file, infile)
                line.psnr.append(psnr[0])
                line.psnr_luam.append(psnr[1])
                line.psnr_charm_cb.append(psnr[2])
                line.psnr_charm_cr.append(psnr[3])
            # com_psnr = Array('d', len(line.output) * 4)
            # for diff_file in range(len(line.output)):
            #     p = Process(target=yuv.psnr_all, args=(diff_file, infile, com_psnr))
            #     p.start()
            #     p_pool.append(p)
            # for p in p_pool:
            #     p.join()
            # for num in range(len(line.output)):
            #     line.psnr.append(com_psnr[num * 4])
            #     line.psnr_luam.append(com_psnr[num * 4 + 1])
            #     line.psnr_charm_cb.append(com_psnr[num * 4 + 2])
            #     line.psnr_charm_cr.append(com_psnr[num * 4 + 3])
            elapsed = (time.time() - time_b)
            m, s = divmod(elapsed, 60)
            h, m = divmod(m, 60)
            print("calculate psnr time used : %d:%02d:%02d" % (h, m, s))
            line.set_average_fps()
            # line.set_bd_psnr(BD.BD_PSNR_Average(line.bit_rate, line.psnr))
            line.sort()


class LineContain:
    def __init__(self, codec_num=None):
        self.baseline = None
        self.codec_num = codec_num
        self.group = {}
        self.group_tag = {}
        self.group_bdrate = {}
        self.yuv_info = None
        self.codec_pipe = {}

    def extra(self):
        return self

    def set_group(self, pool, name):
        self.group[name] = pool

    def add_codec_pipe(self, codec, pipe):
        self.codec_pipe[codec].append(pipe)

    def parse_codec_pipe(self):
        for codec in self.codec_pipe:
            name = codec.split('_')[0]
            for pipe in self.codec_pipe[codec]:
                if name == 'HM':
                    mode_line = pipe.pop_pro_hm()
                else:
                    mode_line = pipe.pop_pro_other()
                if mode_line:
                    self.add_group_ele(codec, mode_line)
                    pipe.clear()
                else:
                    break

    def clean_pipe(self):
        self.codec_pipe.clear()

    def pipe_security(self):
        for codec in self.codec_pipe:
            for pipe in self.codec_pipe[codec]:
                pipe.security()

    def set_data_type(self, yuv_info):
        self.yuv_info = yuv_info

    def set_baseline(self, line):
        self.baseline = line

    def build_group(self, codec):
        for encode in codec:
            self.group[encode[2] + '_' + encode[4]] = []
            self.group_bdrate[encode[2] + '_' + encode[4]] = []
            self.group_tag[encode[2] + '_' + encode[4]] = 1
            self.codec_pipe[encode[2] + '_' + encode[4]] = []

    def add_group_ele(self, codec_name, line):
        self.group[codec_name].append(line)

    def check_baseline_old(self, codec):
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

    def check_baseline(self, option):
        for codec in option:
            if codec[6] == 'baseline':
                self.set_baseline(self.group[codec[2]+'_'+codec[4]][0])
                break

    def set_group_tag(self, codec_name):
        self.group_tag[codec_name] = 0

    def get_bd_rate(self, baseline, line):
        rate = BD.BD_RATE(baseline.bit_rate, baseline.psnr, line.bit_rate, line.psnr)
        psnr_y = BD.BD_RATE(baseline.bit_rate, baseline.psnr_luam, line.bit_rate, line.psnr_luam)
        psnr_u = BD.BD_RATE(baseline.bit_rate, baseline.psnr_charm_cb, line.bit_rate, line.psnr_charm_cb)
        psnr_v = BD.BD_RATE(baseline.bit_rate, baseline.psnr_charm_cr, line.bit_rate, line.psnr_charm_cr)
        rate_y = str(round(psnr_y, 2)) + '%'
        rate_u = str(round(psnr_u, 2)) + '%'
        rate_v = str(round(psnr_v, 2)) + '%'
        return rate, rate_y, rate_u, rate_v

    def get_bd_psnr(self, baseline, line):
        psnr = BD.BD_PSNR(baseline.bit_rate, baseline.psnr, line.bit_rate, line.psnr)
        psnr_y = BD.BD_PSNR(baseline.bit_rate, baseline.psnr_luam, line.bit_rate, line.psnr_luam)
        psnr_u = BD.BD_PSNR(baseline.bit_rate, baseline.psnr_charm_cb, line.bit_rate, line.psnr_charm_cb)
        psnr_v = BD.BD_PSNR(baseline.bit_rate, baseline.psnr_charm_cr, line.bit_rate, line.psnr_charm_cr)
        psnr = str(round(psnr, 2)) + 'dB'
        psnr_y = str(round(psnr_y, 2)) + 'dB'
        psnr_u = str(round(psnr_u, 2)) + 'dB'
        psnr_v = str(round(psnr_v, 2)) + 'dB'
        return psnr, psnr_y, psnr_u, psnr_v

    def calculate_psnr(self):
        for pool in self.group.values():
            for line in pool:
                line.BD_psnr, line.BD_psnr_luam, line.BD_psnr_charm_cb, line.BD_psnr_charm_cr = self.get_bd_psnr(
                    self.baseline, line)
                line.bd_psnr = BD.BD_PSNR_Average(self.baseline.bit_rate, self.baseline.psnr, line.bit_rate, line.psnr)

    def calculate_bd_rate(self):
        for pool in self.group.values():
            for line in pool:
                bd_rate, bd_rate_y, bd_rate_u, bd_rate_v = self.get_bd_rate(self.baseline, line)
                line.bd_rate = bd_rate
                line.bd_rate_luma = bd_rate_y
                line.bd_rate_charm_cb = bd_rate_u
                line.bd_rate_charm_cr = bd_rate_v
                self.group_bdrate[line.codec_name + '_' + line.instance_name].append(bd_rate)

    def calculate(self):
        self.calculate_bd_rate()
        self.calculate_psnr()


class CaseDate:
    def __init__(self, path=None):
        self.case = []
        self.case_group = {'360': [], '480': [], '720': [], '1080': [],
                           '1152': [], '2304': [], '3840': [], }
        self.case_num = None
        self.datafile = None
        self.path = path

    def extra(self):
        return self

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
                    file_line[5] = line.psnr[i]
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
