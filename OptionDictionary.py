# this file we config command line to different codec
# 0 means HM, 1 means x265, 2 means SVT-HEVC

Qp = [22, 28, 34, 40]

config = [
#TargetBitrate
            ['TargetBitrate', ['TargetBitrate', '--bitrate', '-tbr'], ['2000', '2000', '2000']],
#preset
            ['EncoderBitDepth', ['InputBitDepth', '--input-depth', '-bit-depth'], ['8', '8', '8']],
#Profile
            ['Profile', ['Profile', '--profile', '-profile'], ['main', 'main', '1']],
# #IntraPeriod
            ['IntraPeriod', ['IntraPeriod', '--keyint', '-intra-period'], ['32', '32', '32']]
# # QP
#             [['22', '28', '34', '40'], ['-q', '-q', '-q'], 'QP']
]
# BitstreamFile
#             ['/home/cxh/code/exec_py/data/', ['-b',  '-o',  '-b'], 'BitstreamFile'],
'''
#
            ['', ['', '', ''], '']

# the argument that is not common

HorizontalPadding = ['-pdx', '', '']

VerticalPadding = ['-pdy', '', '']

GOPSize = ['-g', '', '']
'''