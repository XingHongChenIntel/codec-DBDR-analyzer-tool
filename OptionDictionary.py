HM_cfg_Path = '/home/cxh/code/HM-16.1/cfg/encoder_randomaccess_main.cfg'

Test_data_type = '360p'

mode = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

codec = [[[25, 29, 34, 38], './TAppEncoderStatic -c %s -fr 60 -f 60' % HM_cfg_Path, 'HM', '265', 'instance name'],
         [[29, 35, 42, 48], './x265 --fps 60', 'x265', '265', 'instance name'],
         [[25, 29, 34, 38], './SvtHevcEncApp', 'svt', '265', 'instance name'],
         ]

codec_dict = {
    'HM': '-i %s -wdt %s -hgt %s -q %s -b %s',
    'x265': '--input %s --input-res %sx%s --input-depth %s -q %s -p %s -o %s',
    'svt': '-i %s -w %s -h %s -bit-depth %s -q %s -encMode %s -b %s',
}

decode_dict = {
    '265': './TAppDecoderStatic -b %s -o %s'
}

TestSequencePath = '/home/cxh/code/codec-DBDR-analyzer-tool/test.csv'

exec_path = {
    'HM': '/home/cxh/code/HM-16.1/bin/',
    'x265': '/home/cxh/code/x265/build/linux/',
    'svt': '/home/cxh/code/SVT-HEVC/Bin/Release/'
}

encodeYuvPath = '/home/cxh/code/codec-DBDR-analyzer-tool/data/'

calculate_data = '/home/cxh/code/data.csv'

plot_path = '/home/cxh/code/pictures/'

Qp = [22, 28, 34, 40]
