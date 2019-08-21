import os
import re
import argparse
import signal
import sys
import visual as tool
import y4mconv as convtool
import exec_method as codec_command
import common_config as Path
import OptionDictionary as option
from exec_method import Codec

#TODO we need make map about codec buffer and codec name
# hm_contain , 'HM'
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


def setup_codec(CodecInfo):
    for qp in option.Qp:
        for j in Codec:
            if j.name == 'HM':
                hm_contain.append(codec_command.exec_HM(CodecInfo, qp))
            else:
                for mode in option.svt_mode:
                    if j.name == 'x265':
                        x265_contain.append(codec_command.exec_x265(CodecInfo, qp, 9-mode))
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

# execute all those codec to encode
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputfile', help='input file name', type=str)
    parser.add_argument('-o', '--outputfile', help='output file name', type=str)
    parser.add_argument('-q', '--QPvalue', help='give a QP list', type=int, nargs='+')
    parser.add_argument('-w', '--SourceWidth', help='picture Source Width', type=int)
    parser.add_argument('-H', '--SourceHeight', help='picture Source Width', type=int)
    parser.add_argument('-r', '--framerate', help='give a frame rate for encode', type=int)
    parser.add_argument('-f', '--frames', help='encoded frames numbers', type=int)
    parser.add_argument('-s', '--svt', help='turn on svt mode', type=int,default=0)
    args = parser.parse_args()
    return args


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


def checkdatadir():
    dirs = os.listdir(Path.encodeYuvPath)
    for i in dirs:
        os.remove(Path.encodeYuvPath + i)


def main():
    args = parse_args()
    checkdatadir()
    TestSequence = Path.TestSequencePath
    contain = Testally4m(TestSequence, args)
    # tool.plot_psnr_frames(contain)


if __name__ == '__main__':
    main()
