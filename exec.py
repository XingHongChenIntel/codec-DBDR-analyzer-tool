import os
import re
import subprocess
import csv
from y4mconv import yuvInfo
import OptionDictionary as option
from Data_struct import Line, LineContain, CaseDate
from UI import UI
import pickle
import argparse
import signal
import time


def decode(codec_name, bit_stream, yuv):
    if codec_name == '265':
        os.chdir(option.exec_path['HM'])
        arg = option.decode_dict[codec_name] % (bit_stream, yuv)
        p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        info = p.communicate()
    else:
        print "we are not ready for 264"


def modify_cfg(opt, value):
    f = open(option.HM_cfg_Path, 'r')
    line = f.read()
    f.close()
    f = open(option.HM_cfg_Path, 'w')
    line = re.sub(r'%s[ ]*:[ ]*[a-zA-Z0-9]*' % opt, '%s     : %s' % (opt, value), line)
    f.write(line)
    f.close()


class ProEnv:
    def __init__(self, p=None, codec_index=None, output=None, yuv=None, qp=None, mode=None):
        self.progress = p
        self.codec_index = codec_index
        self.output = output
        self.yuv = yuv
        self.qp = qp
        self.mode = mode


class Pipeline:
    def __init__(self, line):
        self.pro = []
        self.line = line
        self.drop_tag = False

    def push_pro(self, pro):
        self.pro.append(pro)

    def pop_pro_hm(self):
        for pro in self.pro:
            info = pro.progress.communicate()
            decode(pro.codec_index[3], pro.output, pro.yuv)
            self.line.add_info(info, pro.codec_index)
            self.line.add_output(pro.yuv)
            self.line.add_qp(pro.qp)
        self.line.get_psnr(self.line)
        return self.line

    def pop_pro_other(self):
        for pro in self.pro:
            info = pro.progress.communicate()
            if len(self.line.check_info(info)) is 0:
                self.drop_tag = True
                break
            decode(pro.codec_index[3], pro.output, pro.yuv)
            self.line.add_info(info, pro.codec_index)
            self.line.add_output(pro.yuv)
            self.line.add_qp(pro.qp)
        if self.drop_tag:
            return None
        else:
            self.line.get_psnr(self.line)
            return self.line

    def clear(self):
        if not self.drop_tag:
            for pro in self.pro:
                os.remove(pro.yuv)
                os.remove(pro.output)

    def security(self):
        for pro in self.pro:
            pro.progress.terminate()


def hm_execute(yuv_info, codec_index, line_pool):
    os.chdir(option.exec_path['HM'])
    line = Line([yuv_info.url], 'HM', yuv_info.bit_depth, yuv_info.width, yuv_info.height, 'YV12', yuv_info)
    pipe = Pipeline(line)
    for qp in codec_index[0]:
        output = option.encodeYuvPath + 'HM_%s_%s_' % (codec_index[4], qp) + yuv_info.yuv_name + '.' + codec_index[3]
        yuv = option.encodeYuvPath + 'HM_%s_%s_' % (codec_index[4], qp) + yuv_info.yuv_name + '.' + yuv_info.suffix_type
        arg = codec_index[1] + ' ' + option.codec_dict['HM'] % (yuv_info.url, yuv_info.width,
                                                                yuv_info.height, qp, output)
        print arg
        modify_cfg('InternalBitDepth', yuv_info.bit_depth)
        p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        env = ProEnv(p, codec_index, output, yuv, qp)
        pipe.push_pro(env)

    def signal_handler(signal, frame):
        pipe.security()

    signal.signal(signal.SIGINT, signal_handler)
    return pipe



def codec_execute(yuv_info, codec_index, line_pool):
    codec_name = codec_index[2]
    instance_name = codec_index[4]
    for mode in option.mode:
        line = Line([yuv_info.url], codec_name, yuv_info.bit_depth, yuv_info.width, yuv_info.height, 'YV12', yuv_info)
        pipe = Pipeline(line)
        for qp in codec_index[0]:
            os.chdir(option.exec_path[codec_name])
            output = option.encodeYuvPath + '%s_%s_%s_%s' % (codec_name, instance_name, mode, qp) \
                     + yuv_info.yuv_name + '.' + codec_index[3]
            yuv = option.encodeYuvPath + '%s_%s_%s_%s' % (codec_name, instance_name, mode, qp) \
                  + yuv_info.yuv_name + '.' + yuv_info.suffix_type
            arg = codec_index[1] + ' ' + option.codec_dict[codec_name] % (yuv_info.url, yuv_info.width,
                                                                          yuv_info.height, yuv_info.bit_depth,
                                                                          qp, mode, output)
            print arg
            p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            evn = ProEnv(p, codec_index, output, yuv, qp, mode)
            pipe.push_pro(evn)

        def signal_handler(signal, frame):
            pipe.security()

        signal.signal(signal.SIGINT, signal_handler)
        mode_line = pipe.pop_pro_other()
        if mode_line:
            line_pool.add_group_ele(codec_name + '_' + instance_name, mode_line)
            pipe.clear()
        else:
            break


def setup_codec(yuv_info):
    line_pool = LineContain(len(option.codec))
    line_pool.set_data_type(yuv_info)
    line_pool.build_group(option.codec)
    for codec_index in option.codec:
        if codec_index[2] == 'HM':
            codec_index_hm = codec_index
            pipe_hm = hm_execute(yuv_info, codec_index, line_pool)
        else:
            codec_execute(yuv_info, codec_index, line_pool)
    line_pool.add_group_ele('HM_' + codec_index_hm[4], pipe_hm.pop_pro_hm())
    pipe_hm.clear()
    line_pool.check_baseline(option.codec)
    return line_pool


def clean_data_dir():
    dirs = os.listdir(option.encodeYuvPath)
    for i in dirs:
        os.remove(option.encodeYuvPath + i)


def parse_resolution(resolution):
    resolution_dict = {'360p': 360, '480p': 480, '720p': 720, '1080p': 1080,
                       '2K': 1440, '4K': 2160, '8K': 3840, 'all': None}
    return resolution_dict[resolution]


def read_csv():
    target_yuv = parse_resolution(option.Test_data_type)
    target_yuv_contain = []
    with open(option.TestSequencePath, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0][0] == '#':
                continue
            yuv_info = yuvInfo()
            yuv_info.parse_yuv_type(row[0])
            if target_yuv is None:
                target_yuv_contain.append(yuv_info)
            elif yuv_info.height == str(target_yuv):
                target_yuv_contain.append(yuv_info)
    return target_yuv_contain


def serialize_date(data):
    f = open(option.calculate_serialize_data, 'wb')
    pickle.dump(data, f)
    f.close()


def deserialize_data():
    f = open(option.calculate_serialize_data, 'rb')
    data = pickle.load(f)
    f.close()
    return data


def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--plot', help='if already got data we can just plot', default=0, type=int)
    args = parser.parse_args()
    return args


def run_command():
    clean_data_dir()
    time_b = time.time()
    yuv_contain = read_csv()
    case_data = CaseDate(option.calculate_data)
    print "\ntest case number is %d\n" % len(yuv_contain)
    for yuv in yuv_contain:
        case = setup_codec(yuv)
        case.calculate()
        case_data.add_case(case, yuv)
    case_data.set_case_num()
    case_data.setup_file()
    serialize_date(case_data)
    ui = UI(case_data)
    ui.show()
    elapsed = (time.time() - time_b)
    m, s = divmod(elapsed, 60)
    h, m = divmod(m, 60)
    print("time used : %d:%02d:%02d" % (h, m, s))


def draw_ui():
    case_data = deserialize_data()
    ui = UI(case_data)
    ui.show()


def main():
    args = parse_arg()
    if args.plot is 0:
        run_command()
    else:
        draw_ui()


if __name__ == '__main__':
    main()
