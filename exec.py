import os
import re
import signal
import sys
import subprocess
import csv
import visual as tool
from y4mconv import yuvInfo
import exec_method as codec_command
import common_config as Path
import OptionDictionary as option
from exec_method import Codec
from Data_struct import Line, LineContain, CaseDate

hm_contain = []
x265_contain = []
svt_contain = []


def signal_handler(signal, frame):
    for comboInfo in hm_contain:
        if comboInfo[0].poll() == None:
            comboInfo[0].terminate()
    sys.exit(0)


# extract bitrate from output info
def find_bitrate(codec_name, line):
    if codec_name == 'x265':
        ss = re.findall(r'([\.0-9]*)[\r\n\t ]kb/s', line[1])
        return float(ss[-1])
    elif codec_name == 'SVT':
        ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
        return float(ss[-1])
    elif codec_name == 'HM':
        ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
        return float(ss[-1])


def find_fps(codec_name, line):
    if codec_name == 'x265':
        ss = re.findall(r'\(([\.0-9]*)[\r\n\t ]*fps\)', line[1])
        return float(ss[-1])
    elif codec_name == 'SVT':
        ss = re.findall(r'Average Speed:[\r\n\t ]*([\.0-9]*)[\r\n\t ]*fps', line[0])
        return float(ss[-1])
    elif codec_name == 'HM':
        ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
        return float(ss[-1])


def addbitrate(codec_contain, codec_name):
    bitrate_buffer, output_yuv_path_buffer, fps_buffer = [], [], []
    line, info, common, outputInfo = 0, 1, 0, ''
    for comboInfo in codec_contain:
        if codec_name == 'HM':
            outputInfo = comboInfo[line].communicate()
        else:
            outputInfo = comboInfo[line]
        bitrate_buffer.append(find_bitrate(codec_name, outputInfo))
        output_yuv_path_buffer.append(comboInfo[info][1])
        fps_buffer.append(find_fps(codec_name, outputInfo))
    codec_contain[common][info][1] = output_yuv_path_buffer
    codec_contain[common][info].insert(2, bitrate_buffer)
    codec_contain[common][info].append(fps_buffer)
    signal.signal(signal.SIGINT, signal_handler)
    return codec_contain[common][info]


def settleInfo():
    line_contain = []
    mode_sum = len(option.svt_mode)
    line_contain.append(addbitrate(hm_contain, 'HM'))
    for mode in option.svt_mode:
        line_contain.append(addbitrate(x265_contain[mode::mode_sum], 'x265'))
    for mode in option.svt_mode:
        line_contain.append(addbitrate(svt_contain[mode::mode_sum], 'SVT'))
    signal.signal(signal.SIGINT, signal_handler)
    return line_contain


def setup_codec1(CodecInfo):
    for qp in option.Qp:
        for j in Codec:
            if j.name == 'HM':
                hm_contain.append(codec_command.exec_HM(CodecInfo, qp))
            else:
                for mode in option.svt_mode:
                    if j.name == 'x265':
                        x265_contain.append(codec_command.exec_x265(CodecInfo, qp, 9 - mode))
                    if j.name == 'SVT':
                        svt_contain.append(codec_command.exec_svt(CodecInfo, qp, mode))
    signal.signal(signal.SIGINT, signal_handler)
    return settleInfo()


def setup_svt(CodecInfo):
    svt_contain = []
    for svt in option.svt_Qp:
        for mode in option.svt_mode:
            svt_oneplot_contain = []
            for qp in svt[0]:
                svt_oneplot_contain.append(codec_command.exec_svt_config(CodecInfo, qp, svt[1], mode))
            svt_contain.append(addbitrate(svt_oneplot_contain, 'SVT'))
    return svt_contain


def Testally4m(test_sequence, arg):
    y4mInfo = {'inputfile': '', 'outputfile': '', 'width': 0, 'height': 0, 'format': '',
               'fps': 0, 'frame_count': 0, 'frame_size': 0, 'frame_skip': 0, 'bitdepth': 0}
    contain = []
    dirs = os.listdir(test_sequence)
    case_num, case_count = 0, 0
    for file in dirs:
        if file.split('.')[-1] == 'y4m':
            case_num += 1
    for file in dirs:
        if file.split('.')[-1] == 'y4m':
            case_count += 1
            if case_count is case_num:
                case_count = 0
            y4mInfo['inputfile'] = test_sequence + file
            y4mInfo['outputfile'] = test_sequence + file.split('.')[0] + '.yuv'
            CodecInfo = convtool.from_y4m_to_yuv(y4mInfo)
            if arg.svt is 0:
                tool.plot_psnr_frames(setup_codec(CodecInfo), case_count)
            else:
                tool.plot_psnr_svt(setup_svt(CodecInfo), case_count)
            del hm_contain[:]
            del svt_contain[:]
            del x265_contain[:]
    return contain


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
        line.add_info(info)
        line.add_output(yuv)
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
            line.add_info(info)
            line.add_output(yuv)
        if line_pool.group_tag[codec_name] is 0:
            break
        line_pool.add_group_ele(codec_name, line)


def setup_codec(yuv_info):
    line_pool = LineContain(len(option.codec))
    line_pool.build_group(option.codec)
    for codec_index in option.codec:
        if codec_index[2] == 'HM':
            hm_execute(yuv_info, codec_index, line_pool)
        else:
            codec_execute(yuv_info, codec_index, line_pool)
    line_pool.check_baseline(option.codec)
    signal.signal(signal.SIGINT, signal_handler)
    return line_pool


def clean_data_dir():
    dirs = os.listdir(Path.encodeYuvPath)
    for i in dirs:
        os.remove(Path.encodeYuvPath + i)


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


def main():
    clean_data_dir()
    yuv_contain = read_csv()
    case_data = CaseDate()
    for yuv in yuv_contain:
        case_data.add_case(setup_codec(yuv))
    # contain = Testally4m(TestSequence, args)
    # tool.plot_psnr_frames(contain)


if __name__ == '__main__':
    main()
