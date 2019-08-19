import common_config
import subprocess
import os
import re
from enum import Enum
import OptionDictionary as option


# from OptionDictionary import option

class Codec(Enum):
    HM = 0
    x265 = 1
    SVT = 2


def modify_cfg(opt, value):
    f = open(common_config.cfgPath['HM'], 'r')
    line = f.read()
    f.close()
    f = open(common_config.cfgPath['HM'], 'w')
    line = re.sub(r'%s[ ]*:[ ]*[a-zA-Z0-9]*' % opt, '%s     : %s' % (opt, value), line)
    f.write(line)
    f.close()


def add_options(codec):
    arg = ''
    for opt in option.config:
        if codec == 'HM':
            modify_cfg(opt[1][0], opt[2][0])
        elif codec == 'x265':
            arg += ' ' + opt[1][1] + ' ' + opt[2][1]
        elif codec == 'svt':
            arg += ' ' + opt[1][2] + ' ' + opt[2][2]
    return arg


def exec_HM(yuv_info, config_param):
    # TODO generate args and run args then get info
    os.chdir(common_config.exec_path['HM'])
    arg = './TAppEncoderStatic -c %s -i %s -wdt %s -hgt %s -fr %s -fs %s -f %s' \
          % (common_config.cfgPath['HM'], yuv_info['outputfile'], yuv_info['width'],
             yuv_info['height'], yuv_info['fps'], yuv_info['frame_skip'], yuv_info['frame_count'])
    encode_yuv = common_config.encodeYuvPath + 'HM_%s_' % config_param + yuv_info['outputfile'].split('/')[-1]
    arg += ' -q %d -o %s' % (config_param, encode_yuv)
    add_options('HM')
    print arg
    p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
    # TODO you have to get bitdepet and type
    info = [[yuv_info['outputfile']], encode_yuv, 'HM', 8, yuv_info['width'], yuv_info['height'], 'YV12']
    return [p, info]


def exec_x265(yuv_info, config_param):
    os.chdir(common_config.exec_path['x265'])
    arg = './x265 --input %s --input-res %sx%s --fps %s --frame-skip %s --frames %s -q %d' \
          % (yuv_info['outputfile'], yuv_info['width'], yuv_info['height'], yuv_info['fps'],
             yuv_info['frame_skip'], yuv_info['frame_count'], config_param)
    x265file = yuv_info['outputfile'].split('/')[-1].split('.')[0] + '.265'
    yuvfile = yuv_info['outputfile'].split('/')[-1].split('.')[0] + '.yuv'
    encode_yuv = common_config.encodeYuvPath + 'x265_%s_' % config_param + x265file
    x265yuv = common_config.encodeYuvPath + 'x265_%s_' % config_param + yuvfile
    arg += ' -o %s' % encode_yuv
    arg += add_options('x265')
    print arg

    p = subprocess.Popen(arg, shell=True, stderr=subprocess.PIPE)
    line = p.communicate()
    if line is None:
        print '\ni am x265\n'
    q = subprocess.Popen('ffmpeg -i %s %s' % (encode_yuv, x265yuv), shell=True)
    # TODO you have to get bitdepet and type
    info = [[yuv_info['outputfile']], x265yuv, 'x265', 8, yuv_info['width'], yuv_info['height'], 'YV12']
    return [line, info]


def exec_svt(yuv_info, config_param):
    os.chdir(common_config.exec_path['svt'])
    arg = './SvtHevcEncApp -i %s -w %s -h %s -fps %s -n %s -q %d' \
          % (yuv_info['outputfile'], yuv_info['width'], yuv_info['height'], yuv_info['fps'],
             yuv_info['frame_count'], config_param)
    encode_yuv = common_config.encodeYuvPath + 'svt_%s_' % config_param + yuv_info['outputfile'].split('/')[-1]
    arg += ' -o %s' % encode_yuv
    arg += add_options('svt')
    print arg
    p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
    line = p.communicate()
    if line is None:
        print '\ni am svt\n'
    # TODO you have to get bitdepet and type
    info = [[yuv_info['outputfile']], encode_yuv, 'svt', 8, yuv_info['width'], yuv_info['height'], 'YV12']
    return [line, info]
