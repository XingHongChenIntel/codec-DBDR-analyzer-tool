calculate_serialize_data = '/home/media/Test_Environment/codec-DBDR-analyzer-tool/database'
proxy = '/home/media/Test_Environment/codec-DBDR-analyzer-tool/data/'
# choose the HM cfg file path on your computer
HM_cfg_Path = '/home/media/Test_Environment/HM-16.1/cfg/encoder_randomaccess_main.cfg'

# file path which got test yuv or y4m information.(10 bit y4m isn't available now)
TestSequencePath = '/home/media/Test_Environment/codec-DBDR-analyzer-tool/test.csv'

# encoder path
exec_path = {
    'HM': '/home/media/Test_Environment/HM-16.1/bin/',
    'x265': '/home/media/Test_Environment/x265/build/linux/',
    'svt': '/home/media/Test_Environment/SVT-HEVC/Bin/Release/',
    'AV1': '/home/media/Test_Environment/aom/rebuild/',
    'JM': '/home/media/Test_Environment/JM/bin/',
    'x264': '/home/media/Test_Environment/x264/',
    'SvtAv1': '/home/media/kelvin/av1/2pass/',
}

# test encoder and command line. it will be  QP, command line, encoder name, codec name, instance name,
# is read from database(you can use 'read' or 'execute')
# every time when you add new encode ,you should also add them to exec_path and codec_dict
codec = [#[[25, 29, 34, 38], './TAppEncoderStatic -c %s -fr 60 -f 10000' % HM_cfg_Path, 'HM', '265', 'testmode', 'read'],
        #[[29, 35, 42, 48], './x265 --fps 60', 'x265', '265', 'testmode', 'read'],
        #[[22, 28, 34, 40], './SvtHevcEncApp', 'svt', '265', 'testmode', 'read'],
        #[[29, 35, 42, 48], './SvtHevcEncApp', 'svt', '265', 'test', 'read'],
        #[[25, 31, 37, 43], './aomenc --threads=64', 'AV1', 'AV1', 'Origin', 'execute', 'baseline'],
        #[[22, 28, 34, 40], './x264', 'x264', '264', 'testmode', 'read'],
        [[20, 26, 32, 38], './testorigin.sh', 'SvtAv1','SvtAv1','origin_','execute', 'baseline'],
        [[20, 26, 32, 38], './test2pass.sh', 'SvtAv1','SvtAv1','2pass_','execute', 'none'],
        [[20, 26, 32, 38], './test2pass_stat.sh', 'SvtAv1','SvtAv1','2pass_stat_','execute', 'none'],
        #[[25,],'./aomenc --codec=av1 --passes=2 --threads=64 --i420 --profile=0 --frame-parallel=0 --tile-columns=0 --test-decode=fatal --kf-min-dist=120  --kf-max-dist=120 --end-usage=q --lag-in-frames=25 --auto-alt-ref=2 --aq-mode=0 --fps=30000/1001', 'AV1', 'AV1', 'Qmode', 'execute', 'none'],
        #[[25,],'./aomenc --codec=av1 --passes=2 --threads=64 --i420 --profile=0 --frame-parallel=0 --tile-columns=0 --test-decode=fatal --kf-min-dist=120  --kf-max-dist=120 --end-usage=cq --lag-in-frames=25 --auto-alt-ref=2 --aq-mode=0 --fps=30000/1001', 'AV1', 'AV1', 'CQmode', 'execute', 'none'],
]

# choose the test sample type, for example 360p 720p 1080p 2k 4k 8k
# if you want to test all sample use 'all
Test_data_type = '720p'

# encode mode for different encoder
mode = [0,]#1, 2, 3, 4, 5, 6, 7, 8,]# 9, 10, 11, 12, 13, 14, 15]
# encoder command line parameter about yuv info, if test new encoder, need to add information here
codec_dict = {
    'HM': '-i %s -wdt %s -hgt %s -q %s -b %s',
    'x265': '--input %s --input-res %sx%s --input-depth %s -q %s -p %s -o %s',
    'svt': '-i %s -w %s -h %s -bit-depth %s -q %s -encMode %s -b %s',
    'AV1': ' %s -w %s -h %s -b %s --cq-level=%s --cpu-used=%s --verbose --psnr -o %s',
    'x264': ' %s --input-res %sx%s --input-depth %s -q %s --preset %s -o %s',
    'SvtAv1': '%s %s %s %s %s %s %s /home/media/Test_Environment/codec-DBDR-analyzer-tool/data/',
}

# decoder path
decode_dict = {
    '265': './TAppDecoderStatic -b %s -o %s',
    'AV1': './aomdec --codec=av1 %s -o %s --i420',
    '264': './ldecod.exe -i %s -o %s',
    'SvtAv1': 'ffmpeg -i %s %s',
}

# encode yuv data save path
encodeYuvPath = proxy

# calculate psnr bd_rate
calculate_data = '%sdata.csv' % proxy

# the path to save the plot picture
plot_path = proxy
