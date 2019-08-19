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

hm_contain = []
x265_contain = []
svt_contain = []


def signal_handler(signal, frame):
    for comboInfo in hm_contain:
        if comboInfo[0].poll() is None:
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
    elif codecname == 'HM':
        ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
        return float(ss[-1])


def add_bitrate(codec_contain, codec_name):
    bitrate_buffer, output_yuv_path_buffer = [], []
    line, info, common, outputInfo = 0, 1, 0, ''
    for comboInfo in codec_contain:
        if codec_name == 'HM':
            outputInfo = comboInfo[line].communicate()
        else:
            outputInfo = comboInfo[line]
        bitrate_buffer.append(findbitrate(codecname, outputInfo))
        outyuvpath_buffer.append(comboInfo[info][1])
    codeccontain[common][info][1] = outyuvpath_buffer
    codeccontain[common][info].insert(2, bitrate_buffer)
    signal.signal(signal.SIGINT, signal_handler)
    return codec_contain[common][info]


def settle_info():
    signal.signal(signal.SIGINT, signal_handler)
    return [add_bitrate(hm_contain, 'HM'), add_bitrate(x265_contain, 'x265'), add_bitrate(svt_contain, 'SVT')]


def setup_codec(codec_info):
    for qp in option.Qp:
        for j in Codec:
            if j.name == 'HM':
                hm_contain.append(codec_command.exec_HM(codec_info, qp))
            if j.name == 'x265':
                x265_contain.append(codec_command.exec_x265(codec_info, qp))
            if j.name == 'SVT':
                svt_contain.append(codec_command.exec_svt(codec_info, qp))
    signal.signal(signal.SIGINT, signal_handler)
    return settle_info()


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
    args = parser.parse_args()
    return args


def test_all_y4m(test_sequence):
    y4mInfo = {'inputfile': '', 'outputfile': '', 'width': 0, 'height': 0, 'format': '',
               'fps': 0, 'frame_count': 0, 'frame_size': 0, 'frame_skip': 0}
    contain = []
    dirs = os.listdir(test_sequence)
    for file in dirs:
        if file.split('.')[-1] == 'y4m':
            y4mInfo['inputfile'] = TestSequence + file
            y4mInfo['outputfile'] = TestSequence + file.split('.')[0] + '.yuv'
            CodecInfo = convtool.fromy4m2yuv(y4mInfo)
            contain.extend(setup_codec(CodecInfo))
            del hm_contain[:]
            del svt_contain[:]
            del x265_contain[:]
    return contain


def check_data_dir():
    dirs = os.listdir(Path.encodeYuvPath)
    for i in dirs:
        os.remove(Path.encodeYuvPath + i)


def main():
    args = parse_args()
    check_data_dir()
    TestSequence = Path.TestSequencePath
    contain = test_all_y4m(TestSequence)
    tool.plot_psnr_frames(contain)


if __name__ == '__main__':
    main()
