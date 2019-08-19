#!/usr/bin/env python
import json
import re
import sys
import os
from optparse import OptionParser

def from_y4m_to_yuv(options):
    """ takes a y4m file and transforms it into a raw yuv file """
    in_file = open(options['inputfile'], 'rb')

    header = in_file.readline()
    width = (re.compile("W(\d+)").findall(header))[0]
    height = (re.compile("H(\d+)").findall(header))[0]
    (fpsnum, fpsden) = (re.compile("F(\d+):(\d+)").findall(header))[0]

    framesize = int(width)*int(height)*3/2

    options['width'] = width
    options['height'] = height
    options['frame_size'] = framesize
    fpsden = int(fpsden)*(int(options['frame_skip'])+int(1))
    options['fps'] = int(fpsnum)/fpsden
    options['format'] = '420P'

    if options['outputfile'] is None:
        in_file.close()
        return options

    out_file = open(options['outputfile'], 'wb')
    c=0
    fs = 0
    if options['frame_skip'] > 0:
        print("frame_skip is on. framerate {0}/{1} => {2}/{3}".format(fpsnum,fpsden,options['fpsnum'],options['fpsden']))

    #FIXME this needs to support other formats than 420
    while True:
        frame_header = in_file.readline()
        if frame_header.startswith('FRAME') is False:
            print('\nEnd of Sequence')
            break
        frame = in_file.read(framesize)
        fs+=1

        if fs >= options['frame_skip']+1:
            out_file.write(frame)

            sys.stdout.write("\r{0}".format(c));
            sys.stdout.flush()
            c+=1
            fs=0

    options['frame_count'] = c
    in_file.close()
    out_file.close()
    return options
