# this file we config command line to different codec
# 0 means HM, 1 means x265, 2 means SVT-HEVC
# those for the svt/x265/HM

Qp = [22, 28, 34, 40]
svt_mode = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

config = [
    # TargetBitrate
    # ['TargetBitrate', ['TargetBitrate', '--bitrate', '-tbr'], ['2000', '2000', '2000']],
    # Profile
    ['Profile', ['Profile', '--profile', '-profile'], ['main', 'main', '1']],
    # #IntraPeriod
    ['IntraPeriod', ['IntraPeriod', '--keyint', '-intra-period'], ['32', '32', '32']],
    # MaxFALL
    ['MaxFALL', ['Profile', '--max-cll', '-max-fall'], ['main', '1000,400', '0']],
    # MaxFALL
    # ['MaxFALL', ['Profile', '--max-cll', '-max-fall'], ['main', '1000,400', '0']],
]

# those for the svt with different  configure


svt_Qp = [[[25, 29, 34, 38], '/home/cxh/code/SVT-HEVC/Config/Sample.cfg', 'HEVC'],
          [[29, 35, 42, 48], '/home/cxh/code/SVT-HEVC/Config/Sample.cfg', 'svt1']]

svt_cfgpath = ['/home/cxh/code/SVT-HEVC/Config/Sample.cfg',
               '/home/cxh/code/SVT-HEVC/Config/Sample.cfg']

