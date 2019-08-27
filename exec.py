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


def decode(codec_name, bit_stream, yuv):
    if codec_name == '265':
        os.chdir(option.exec_path['HM'])
        arg = option.decode_dict[codec_name] % (bit_stream, yuv)
        p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
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


def hm_execute(yuv_info, codec_index, line_pool):
    os.chdir(option.exec_path['HM'])
    line = Line([yuv_info.url], 'HM', yuv_info.bit_depth, yuv_info.width, yuv_info.height, 'YV12', yuv_info)
    for qp in codec_index[0]:
        output = option.encodeYuvPath + 'HM_%s_' % (qp) + yuv_info.yuv_name + '.' + codec_index[3]
        yuv = option.encodeYuvPath + 'HM_%s_' % (qp) + yuv_info.yuv_name + '.' + yuv_info.suffix_type
        arg = codec_index[1] + ' ' + option.codec_dict['HM'] % (yuv_info.url, yuv_info.width,
                                                                yuv_info.height, qp, output)
        print arg
        modify_cfg('InternalBitDepth', yuv_info.bit_depth)
        p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        info = p.communicate()
        decode(codec_index[3], output, yuv)
        line.add_info(info, codec_index)
        line.add_output(yuv)
        line.add_qp(qp)
    line_pool.add_group_ele('HM', line)


def codec_execute(yuv_info, codec_index, line_pool):
    codec_name = codec_index[2]
    for mode in option.mode:
        line = Line([yuv_info.url], codec_name, yuv_info.bit_depth, yuv_info.width, yuv_info.height, 'YV12', yuv_info)
        for qp in codec_index[0]:
            os.chdir(option.exec_path[codec_name])
            output = option.encodeYuvPath + '%s_%s_%s_' % (codec_index[2], mode, qp) \
                     + yuv_info.yuv_name + '.' + codec_index[3]
            yuv = option.encodeYuvPath + '%s_%s_%s_' % (codec_index[2], mode, qp) \
                  + yuv_info.yuv_name + '.' + yuv_info.suffix_type
            arg = codec_index[1] + ' ' + option.codec_dict[codec_name] % (yuv_info.url, yuv_info.width,
                                                                          yuv_info.height, yuv_info.bit_depth,
                                                                          qp, mode, output)
            print arg
            p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            info = p.communicate()
            if len(line.check_info(info)) is 0:
                line_pool.set_group_tag(codec_name)
                break
            decode(codec_index[3], output, yuv)
            line.add_info(info, codec_index)
            line.add_output(yuv)
            line.add_qp(qp)
        if line_pool.group_tag[codec_name] is 0:
            break
        line_pool.add_group_ele(codec_name, line)


def setup_codec(yuv_info):
    line_pool = LineContain(len(option.codec))
    line_pool.set_data_type(yuv_info)
    line_pool.build_group(option.codec)
    for codec_index in option.codec:
        if codec_index[2] == 'HM':
            hm_execute(yuv_info, codec_index, line_pool)
        else:
            codec_execute(yuv_info, codec_index, line_pool)
    line_pool.check_baseline(option.codec)
    return line_pool


def clean_data_dir():
    dirs = os.listdir(option.encodeYuvPath)
    for i in dirs:
        os.remove(option.encodeYuvPath + i)


def parse_resolution(resolution):
    resolution_dict = {'360p': 360, '480p': 480, '720p': 720, '1080p': 1080,
                       '2K': 1152, '4K': 2304, '8K': 3840, 'all': None}
    return resolution_dict[resolution]


def read_csv():
    target_yuv = parse_resolution(option.Test_data_type)
    target_yuv_contain = []
    with open(option.TestSequencePath, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
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
    yuv_contain = read_csv()
    case_data = CaseDate(option.calculate_data)
    for yuv in yuv_contain:
        case = setup_codec(yuv)
        case.calculate()
        case_data.add_case(case, yuv)
    case_data.set_case_num()
    case_data.setup_file()
    serialize_date(case_data)
    ui = UI(case_data)
    ui.show()


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
