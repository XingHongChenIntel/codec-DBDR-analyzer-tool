import re
import sys
import OptionDictionary as option


class yuvInfo:
    def __init__(self):
        self.url = None
        self.width = None
        self.height = None
        self.bit_depth = None
        self.color_format = None
        self.yuv_name = None
        self.suffix_type = None
        self.type = 0

    def __eq__(self, other):
        if self.url == other.url and self.width == other.width and self.height == other.height:
            return True
        else:
            return False

    def __ne__(self, other):
        if self.url != other.url or self.width != other.width and self.height != other.height:
            return True
        else:
            return False

    def parse_yuv_type(self, str):
        yuv_info = str.split(' ')
        name = yuv_info[0].split('/')[-1].split('.')
        self.suffix_type = name[1]
        self.yuv_name = name[0]
        if self.suffix_type == 'y4m':
            yuv_info = self.__from_y4m_to_yuv(yuv_info)
        self.suffix_type = 'yuv'
        self.url = yuv_info[0]
        self.width = yuv_info[1]
        self.height = yuv_info[2]
        self.bit_depth = yuv_info[3]
        self.color_format = yuv_info[4]

    def __from_y4m_to_yuv(self, yuv_info):
        """ takes a y4m file and transforms it into a raw yuv file """
        in_file = open(yuv_info[0], 'rb')
        header = in_file.readline()
        width = (re.compile("W(\d+)").findall(header))[0]
        height = (re.compile("H(\d+)").findall(header))[0]
        bit_depth = re.findall(r'XYSCSS=([0-9]*)JPEG', header)
        frame_size = int(width) * int(height) * 3 / 2
        yuv_info.append(width)
        yuv_info.append(height)
        if bit_depth:
            yuv_info.append('8')
        else:
            yuv_info.append('10')
        if yuv_info[0] is None:
            in_file.close()
            return None
        yuv_info[0] = option.encodeYuvPath + self.yuv_name + '.yuv'
        out_file = open(yuv_info[0], 'wb')
        c = 0
        fs = 0
        # FIXME this needs to support other formats than 420
        yuv_info.append('1')
        while True:
            frame_header = in_file.readline()
            if frame_header.startswith('FRAME') is False:
                print('\nEnd of Sequence')
                break
            frame = in_file.read(frame_size)
            fs += 1
            if fs >= 1:
                out_file.write(frame)
                sys.stdout.write("\r{0}".format(c))
                sys.stdout.flush()
                c += 1
                fs = 0
        in_file.close()
        out_file.close()
        return yuv_info
