import os
import re
import argparse
import signal
import sys
import visual as tool
import y4mconv as convtool
import exec_method as codec_command
import common_config as Path
from exec_method import Codec

hm_contain = []
x265_contain = []
svt_contain = []


def signal_handler(signal, frame):
    for comboInfo in hm_contain:
        if comboInfo[0].poll() == None:
            comboInfo[0].terminate()
    sys.exit(0)


# extract bitrate from output info
def findbitrate(codecname, line):
    if codecname == 'x265':
        ss = re.findall(r'([\.0-9]*)[\r\n\t ]kb/s', line[1])
        return float(ss[-1])
    elif codecname == 'SVT':
        ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
        return float(ss[-1])
    elif codecname == 'HM':
        ss = re.findall(r'([\.0-9]*)[\r\n\t ]kbps', line[0])
        return float(ss[-1])


def addbitrate(codeccontain, codecname):
    bitrate_buffer, outyuvpath_buffer = [], []
    line, info, common, outputInfo = 0, 1, 0, ''
    for comboInfo in codeccontain:
        if codecname == 'HM':
            outputInfo = comboInfo[line].communicate()
        else:
            outputInfo = comboInfo[line]
        bitrate_buffer.append(findbitrate(codecname, outputInfo))
        outyuvpath_buffer.append(comboInfo[info][1])
    codeccontain[common][info][1] = outyuvpath_buffer
    codeccontain[common][info].insert(2, bitrate_buffer)
    print '\n'
    print bitrate_buffer
    print '\n'
    signal.signal(signal.SIGINT, signal_handler)
    return codeccontain[common][info]


def settleInfo():
    signal.signal(signal.SIGINT, signal_handler)
    return [addbitrate(hm_contain, 'HM'), addbitrate(x265_contain, 'x265'), addbitrate(svt_contain, 'SVT')]


def setup_codec(CodecInfo):
    for qp in Path.Qp:
        for j in Codec:
            if j.name == 'HM':
                hm_contain.append(codec_command.exec_HM(CodecInfo, qp))
            if j.name == 'x265':
                x265_contain.append(codec_command.exec_x265(CodecInfo, qp))
            if j.name == 'SVT':
                svt_contain.append(codec_command.exec_svt(CodecInfo, qp))
    signal.signal(signal.SIGINT, signal_handler)
    return settleInfo()


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


def Testally4m(TestSequence):
    y4mInfo = {'inputfile': '', 'outputfile': '', 'width': 0, 'height': 0, 'format': '',
               'fps': 0, 'frame_count': 0, 'frame_size': 0, 'frame_skip': 0}
    contain = []
    dirs = os.listdir(TestSequence)
    for file in dirs:
        if file.split('.')[-1] == 'y4m':
            y4mInfo['inputfile'] = TestSequence + file
            y4mInfo['outputfile'] = TestSequence + file.split('.')[0] + '.yuv'
            CodecInfo = convtool.fromy4m2yuv(y4mInfo)
            print CodecInfo
            contain.extend(setup_codec(CodecInfo))
            del hm_contain[:]
            del svt_contain[:]
            del x265_contain[:]
    return contain


def main():
    args = parse_args()
    TestSequence = Path.TestSequencePath
    contain = Testally4m(TestSequence)
    tool.plot_psnr_frames(contain)


if __name__ == '__main__':
    main()
