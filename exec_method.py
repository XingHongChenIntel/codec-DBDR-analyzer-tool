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

def Modifycfg(opt, value):
    f = open(common_config.cfgPath['HM'], 'r')
    line = f.read()
    f.close()
    f = open(common_config.cfgPath['HM'], 'w')
    line = re.sub(r'%s[ ]*:[ ]*[a-zA-Z0-9]*'%opt, '%s     : %s'%(opt, value), line)
    f.write(line)
    f.close()


def Addoptions(codec, bitdepth=0):
    arg = ''
    if not bitdepth:
        Modifycfg('InputBitDepth', bitdepth)
    for opt in option.config:
        if codec == 'HM':
            Modifycfg(opt[1][0], opt[2][0])
        elif codec == 'x265':
            arg += ' '+opt[1][1]+' '+opt[2][1]
        elif codec == 'svt':
            arg += ' '+opt[1][2]+' '+opt[2][2]
    return arg


def exec_HM(yuvInfo, configparam):
    #TODO generate args and run args then get info
    os.chdir(common_config.exec_path['HM'])
    arg = './TAppEncoderStatic -c %s -i %s -wdt %s -hgt %s -fr %s -fs %s -f %s'\
          %(common_config.cfgPath['HM'], yuvInfo['outputfile'], yuvInfo['width'],
            yuvInfo['height'],yuvInfo['fps'], yuvInfo['frame_skip'], yuvInfo['frame_count'])
    encodeyuv = common_config.encodeYuvPath + 'HM_%s_'%(configparam) + yuvInfo['outputfile'].split('/')[-1]
    arg += ' -q %d -o %s'%(configparam, encodeyuv)
    Addoptions('HM', yuvInfo['bitdepth'])
    p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
    #TODO you have to get bitdepet and type
    info = [[yuvInfo['outputfile']], encodeyuv, 'HM', yuvInfo['bitdepth'], yuvInfo['width'], yuvInfo['height'], 'YV12']
    return [p, info]

def exec_x265(yuvInfo,configparam):
    os.chdir(common_config.exec_path['x265'])
    arg = './x265 --input %s --input-res %sx%s --fps %s --frame-skip %s --frames %s --input-depth %d -q %d'\
          %(yuvInfo['outputfile'], yuvInfo['width'], yuvInfo['height'], yuvInfo['fps'],
            yuvInfo['frame_skip'], yuvInfo['frame_count'], yuvInfo['bitdepth'], configparam)
    x265file = yuvInfo['outputfile'].split('/')[-1].split('.')[0]+'.265'
    yuvfile = yuvInfo['outputfile'].split('/')[-1].split('.')[0]+'.yuv'
    encodeyuv = common_config.encodeYuvPath + 'x265_%s_'%(configparam) + x265file
    x265yuv = common_config.encodeYuvPath + 'x265_%s_'%(configparam) + yuvfile
    arg += ' -o %s'%(encodeyuv)
    arg += Addoptions('x265')
    p = subprocess.Popen(arg, shell=True, stderr=subprocess.PIPE)
    line = p.communicate()
    if line == None:
        print '\ni am x265\n'
    q = subprocess.Popen('ffmpeg -i %s %s'%(encodeyuv, x265yuv), shell=True)
    #TODO you have to get bitdepet and type
    info = [[yuvInfo['outputfile']], x265yuv, 'x265', yuvInfo['bitdepth'], yuvInfo['width'], yuvInfo['height'], 'YV12']
    return [line, info]

def exec_svt(yuvInfo,configparam):
    os.chdir(common_config.exec_path['svt'])
    arg = './SvtHevcEncApp -i %s -w %s -h %s -fps %s -n %s -bit-depth %d -q %d'\
          %(yuvInfo['outputfile'], yuvInfo['width'], yuvInfo['height'], yuvInfo['fps'],
            yuvInfo['frame_count'], yuvInfo['bitdepth'], configparam)
    encodeyuv = common_config.encodeYuvPath + 'svt_%s_'%(configparam) + yuvInfo['outputfile'].split('/')[-1]
    arg += ' -o %s'%(encodeyuv)
    arg += Addoptions('svt')
    p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
    line = p.communicate()
    if line == None:
        print '\ni am svt\n'
    #TODO you have to get bitdepet and type
    info = [[yuvInfo['outputfile']], encodeyuv, 'svt', yuvInfo['bitdepth'], yuvInfo['width'], yuvInfo['height'], 'YV12']
    return [line, info]


def exec_svt_config(yuvInfo, configparam, cfg, mode):
    os.chdir(common_config.exec_path['svt'])
    arg = './SvtHevcEncApp -c %s -i %s -w %s -h %s -fps %s -n %s -bit-depth %d -q %d -encMode %d'\
          %(cfg, yuvInfo['outputfile'], yuvInfo['width'], yuvInfo['height'], yuvInfo['fps'],
            yuvInfo['frame_count'], yuvInfo['bitdepth'], configparam, mode)
    encodeyuv = common_config.encodeYuvPath + 'svt_%s_%d'%(configparam, mode) + yuvInfo['outputfile'].split('/')[-1]
    arg += ' -o %s'%(encodeyuv)
    # arg += Addoptions('svt')
    print arg
    p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
    line = p.communicate()
    if line == None:
        print '\ni am svt\n'
    #TODO you have to get bitdepet and type
    info = [[yuvInfo['outputfile']], encodeyuv, 'svt_%d'%(mode), yuvInfo['bitdepth'], yuvInfo['width'], yuvInfo['height'], 'YV12']
    return [line, info]