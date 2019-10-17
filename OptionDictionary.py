calculate_serialize_data = '/home/cxh/code/codec-DBDR-analyzer-tool/database'
proxy = '/home/cxh/code/codec-DBDR-analyzer-tool/data/'
# choose the HM cfg file path on your computer
HM_cfg_Path = '/home/cxh/code/HM-16.1/cfg/encoder_randomaccess_main.cfg'
HM_10_cfg_Path = '/home/cxh/code/HM-16.1/cfg/encoder_randomaccess_main10.cfg'

# file path which got test yuv or y4m information.(10 bit y4m isn't available now)
TestSequencePath = '/home/cxh/code/codec-DBDR-analyzer-tool/test.csv'

# encoder path
exec_path = {
    'HM': '/home/cxh/code/HM-16.1/bin/',
    'x265': '/home/cxh/code/x265/build/linux/',
    'svt': '/home/cxh//code/svt-hevc-master-039366e/BDRate-patch/encoders/039366e/',
    'AV1': '/home/cxh/code/aom/cxhbuild/',
    'JM': '/home/cxh/code/JM/bin/',
    'x264': '/home/cxh/code/x264/',
    'SvtAv1': '/home/cxh/code/SVT-AV1/Bin/Release/'
}

# test encoder and command line. it will be  QP, command line, encoder name, codec name, instance name,
# is read from database(you can use 'read' or 'execute')
# every time when you add new encode ,you should also add them to exec_path and codec_dict
codec = [#[[25, 29, 34, 38], './TAppEncoderStatic -c %s -fr 60 -f 60', 'HM', '265', 't3', 'reae', 'baseline'],
         # [[25, 29, 34, 38], './TAppEncoderStatic -c %s -fr 60', 'HM', '265', 't3', 'reae', 'None'],
        # [[29, 35, 42, 48], './x265 --fps 60', 'x265', '265', 'test265', 're', 'None'],
        # [[22, 28, 34, 40], './SvtHevcEncApp', 'svt', '265', 'testmode', 're', 'baseline'],
        [[22, 27, 32, 37], './SvtHevcEncApp -fps 60 -intra-period 55 -n 30', 'svt', '265', 'vailiate', 're', 'baseline'],
        # [[22, 28, 34, 40], './SvtHevcEncApp', 'svt', '265', 'test', 're', 'None'],
        # [[22, 28, 34, 40], './SvtHevcEncApp', 'svt', '265', 'tes', 're', 'None'],
        # [[22, 28, 34, 40], './aomenc --threads=64', 'AV1', 'AV1', 'testmo', 'rea', 'baseline'],
        # [[22, 28, 34, 40], './aomenc --threads=64', 'AV1', 'AV1', 'tes', 'rea', 'None'],
        # [[22, 28, 34, 40], './aomenc --threads=64', 'AV1', 'AV1', 'testqwe', 'rea', 'None'],
        #[[22, 28, 34, 40], './x264', 'x264', '264', 'testmode', 'read'],
        # [[20, 32, 43, 55], './SvtAv1EncApp -n 60 -intra-period 119 -c /home/cxh/code/SVT-AV1/Config/Sample.cfg \
        #  -lad 119', 'SvtAv1', 'AV1', 'svtav1', 'rea1', 'baseline'],
        # [[20, 32, 43, 55], './SvtAv1EncApp -n 60 -intra-period 119 -c /home/cxh/code/SVT-AV1/Config/Sample.cfg \
        #  -lad 119', 'SvtAv1', 'AV1', 'sv', 'rea1', 'None'],
        # [[20, 32, 43, 55], './aomenc --codec=av1 --psnr --verbose --passes=1 --threads=40 --i420 --profile=0 \
        # --frame-parallel=0 --tile-columns=0 --test-decode=fatal --kf-min-dist=120 --kf-max-dist=120 --end-usage=q \
        # --lag-in-frames=25  --auto-alt-ref=2 --aq-mode=0 --bit-depth=8 --fps=30000/1000', \
        #  'AV1', 'AV1', 'av1', 'read', 'baseline'],
]

# choose the test sample type, for example 360p 720p 1080p 2K 4K 8K
# if you want to test all sample use 'all
Test_data_type = 'all'
Multi_process = 1
# encode mode for different encoder
mode = [0,] # 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
# encoder command line parameter about yuv info, if test new encoder, need to add information here
codec_dict = {
    'HM': '-i %s -wdt %s -hgt %s -q %s -b %s',
    'x265': '--input %s --input-res %sx%s --input-depth %s -q %s -p %s -o %s',
    'svt': '-i %s -w %s -h %s -bit-depth %s -q %s -encMode %s -b %s -color-format %s',
    'AV1': ' %s --width=%s --height=%s --input-bit-depth=%s --cq-level=%s --cpu-used=%s -o %s',
    'x264': ' %s --input-res %sx%s --input-depth %s -q %s --preset %s -o %s',
    'SvtAv1': '-i %s -w %s -h %s -bit-depth %s -q %s -enc-mode %s -b %s'
}

# decoder path
decode_dict = {
    '265': './TAppDecoderStatic -b %s -o %s',
    'AV1': './aomdec --codec=av1 %s -o %s --i420',
    '264': './ldecod.exe -i %s -o %s',
    'SvtAv1': './aomdec --codec=av1 %s -o %s --i420',
}

# encode yuv data save path
encodeYuvPath = proxy

# calculate psnr bd_rate
calculate_data = '%s/data.csv' % proxy

# the path to save the plot picture
plot_path = proxy

TestTag = False
