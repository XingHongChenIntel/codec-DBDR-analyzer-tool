import os
import subprocess
import sys
import time
import OptionDictionary as option


def decode(codec_name, bit_stream, yuv, line):
    if int(line.yuv_info.color_format) > 2:
        p = subprocess.Popen('ffmpeg -i %s %s' % (bit_stream, yuv), shell=True, stdout=subprocess.PIPE)
        return p
    if codec_name == '265':
        os.chdir(option.exec_path['HM'])
        arg = option.decode_dict[codec_name] % (bit_stream, yuv)
        p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        return p
    elif codec_name == '264':
        os.chdir(option.exec_path['JM'])
        arg = option.decode_dict[codec_name] % (bit_stream, yuv)
        p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        return p
    elif codec_name == 'AV1':
        os.chdir(option.exec_path['AV1'])
        arg = option.decode_dict[codec_name] % (bit_stream, yuv)
        p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        return p
    elif codec_name == 'SvtAv1':
        os.chdir(option.exec_path['SvtAv1'])
        arg = option.decode_dict[codec_name] % (bit_stream, yuv)
        p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        return p
    else:
        print "we are not ready for this codec"


class ProEnv:
    def __init__(self, p=None, codec_index=None, output=None, yuv=None, qp=None, mode=None, time_begin=None):
        self.progress = p
        self.codec_index = codec_index
        self.output = output
        self.yuv = yuv
        self.qp = qp
        self.mode = mode
        self.time_begin = time_begin


class Pipeline:
    def __init__(self, line):
        self.pro = []
        self.line = line
        self.drop_tag = False

    def push_pro(self, pro):
        self.pro.append(pro)

    def pop_pro_hm(self):
        decode_p_pool = []
        for pro in self.pro:
            info = pro.progress.communicate()
            if len(self.line.check_info(info)) is 0:
                print >> sys.stderr, 'codec:%s, at mode:%s, qp:%s, run failed' % (pro.codec_index, pro.mode, pro.qp)
                self.drop_tag = True
                break
            self.line.add_bitrate(self.line, pro.output)
            p = decode(pro.codec_index[3], pro.output, pro.yuv, self.line)
            decode_p_pool.append(p)
            self.line.add_info(info, pro.codec_index)
            self.line.add_output_url(pro.yuv)
            self.line.add_qp(pro.qp)
            elapsed = (time.time() - pro.time_begin)
            m, s = divmod(elapsed, 60)
            h, m = divmod(m, 60)
            print("encode yuv time used : %d:%02d:%02d" % (h, m, s))
        if self.drop_tag:
            return None
        else:
            for p in decode_p_pool:
                p.communicate()
            self.line.get_psnr(self.line)
            return self.line

    def pop_pro_other(self):
        decode_p_pool = []
        for pro in self.pro:
            info = pro.progress.communicate()
            if len(self.line.check_info(info)) is 0:
                print >> sys.stderr, 'codec:%s, at mode:%s, qp:%s, run failed' % (pro.codec_index, pro.mode, pro.qp)
                print info
                self.drop_tag = True
                break
            self.line.add_bitrate(self.line, pro.output)
            p = decode(pro.codec_index[3], pro.output, pro.yuv, self.line)
            decode_p_pool.append(p)
            self.line.add_info(info, pro.codec_index)
            self.line.add_output_url(pro.yuv)
            self.line.add_qp(pro.qp)
            elapsed = (time.time() - pro.time_begin)
            m, s = divmod(elapsed, 60)
            h, m = divmod(m, 60)
            print("encode yuv time used : %d:%02d:%02d" % (h, m, s))
        if self.drop_tag:
            return None
        else:
            for p in decode_p_pool:
                p.communicate()
            if int(self.line.yuv_info.color_format) == 1:
                self.line.get_psnr(self.line)
            else:
                self.line.get_psnr_ffmpeg(self.line)
            return self.line

    def clear(self):
        if not self.drop_tag:
            for pro in self.pro:
                if not option.TestTag:
                    os.remove(pro.yuv)
                    os.remove(pro.output)

    def security(self):
        print 'kill progress!'
        for pro in self.pro:
            pro.progress.terminate()
