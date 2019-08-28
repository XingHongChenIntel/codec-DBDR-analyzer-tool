# choose the HM cfg file path on your computer
HM_cfg_Path = '/home/cxh/code/HM-16.1/cfg/encoder_randomaccess_main.cfg'

# choose the test sample type, for example 360p 720p 1080p 2k 4k 8k
# if you want to test all sample use 'all
Test_data_type = 'all'

# encode mode for different encoder
mode = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

# test encoder and command line. it will be  QP, command line, encoder name, codec name, instance name
codec = [#[[25, 29, 34, 38], './TAppEncoderStatic -c %s -fr 60 -f 60' % HM_cfg_Path, 'HM', '265', 'instance'],
         #[[29, 35, 42, 48], './x265 --fps 60', 'x265', '265', 'instance'],
         [[25, 29, 34, 38], './SvtHevcEncApp', 'svt', '265', 'instance'],
         ]

# encoder command line parameter about yuv info, if test new encoder, need to add information here
codec_dict = {
    'HM': '-i %s -wdt %s -hgt %s -q %s -b %s',
    'x265': '--input %s --input-res %sx%s --input-depth %s -q %s -p %s -o %s',
    'svt': '-i %s -w %s -h %s -bit-depth %s -q %s -encMode %s -b %s',
}

# decoder path
decode_dict = {
    '265': './TAppDecoderStatic -b %s -o %s'
}

# file path which got test yuv or y4m information
TestSequencePath = '/home/cxh/code/codec-DBDR-analyzer-tool/test.csv'

# encoder path
exec_path = {
    'HM': '/home/cxh/code/HM-16.1/bin/',
    'x265': '/home/cxh/code/x265/build/linux/',
    'svt': '/home/cxh/code/SVT-HEVC/Bin/Release/'
}

# encode yuv data save path
encodeYuvPath = '/home/cxh/code/codec-DBDR-analyzer-tool/data/'

# calculate psnr bd_rate
calculate_data = '/home/cxh/code/data.csv'
# when you use this data to draw plot,
# you have to sure you got same codec information when you run them
calculate_serialize_data = '/home/cxh/code/file_test'
# the path to save the plot picture
plot_path = '/home/cxh/code/pictures/'

