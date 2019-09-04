import os
import re
import subprocess
import csv
import argparse
import time
from y4mconv import yuvInfo
import OptionDictionary_performence as option
from Data_struct import Line, LineContain, CaseDate
from Data_base import Database
from UI_performence import UI


def decode(codec_name, bit_stream, yuv):
    if codec_name == '265':
        os.chdir(option.exec_path['HM'])
        arg = option.decode_dict[codec_name] % (bit_stream, yuv)
        p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        info = p.communicate()
    else:
        print "we are not ready for 264"


def modify_cfg(opt, value):
    f = open(option.HM_cfg_Path, 'r')
    line = f.read()
    f.close()
    f = open(option.HM_cfg_Path, 'w')
    line = re.sub(r'%s[ ]*:[ ]*[a-zA-Z0-9]*' % opt, '%s     : %s' % (opt, value), line)
    f.write(line)
    f.close()


def hm_execute(yuv_info, codec_index, line_pool, database):
    os.chdir(option.exec_path['HM'])
    line = Line([yuv_info.url], 'HM', yuv_info.bit_depth, yuv_info.width, yuv_info.height, 'YV12', yuv_info)
    release_contain = []
    for qp in codec_index[0]:
        output = option.encodeYuvPath + 'HM_%s_%s_' % (codec_index[4], qp) + yuv_info.yuv_name + '.' + codec_index[3]
        yuv = option.encodeYuvPath + 'HM_%s_%s_' % (codec_index[4], qp) + yuv_info.yuv_name + '.' + yuv_info.suffix_type
        arg = codec_index[1] + ' ' + option.codec_dict['HM'] % (yuv_info.url, yuv_info.width,
                                                                yuv_info.height, qp, output)
        print arg
        modify_cfg('InternalBitDepth', yuv_info.bit_depth)
        p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        info = p.communicate()
        decode(codec_index[3], output, yuv)
        line.add_info(info, codec_index)
        line.add_output(yuv)
        line.add_qp(qp)
        release_contain.append([output, yuv])
    line.get_psnr(line)
    line_pool.add_group_ele('HM_' + codec_index[4], line)
    database.add_data(line, 'HM_' + codec_index[4])
    for item in release_contain:
        os.remove(item[0])
        os.remove(item[1])


def codec_execute(yuv_info, codec_index, line_pool, database):
    codec_name = codec_index[2]
    instance_name = codec_index[4]
    for mode in option.mode:
        line = Line([yuv_info.url], codec_name, yuv_info.bit_depth, yuv_info.width, yuv_info.height, 'YV12', yuv_info)
        release_contain = []
        for qp in codec_index[0]:
            os.chdir(option.exec_path[codec_name])
            output = option.encodeYuvPath + '%s_%s_%s_%s' % (codec_name, instance_name, mode, qp) \
                     + yuv_info.yuv_name + '.' + codec_index[3]
            yuv = option.encodeYuvPath + '%s_%s_%s_%s' % (codec_name, instance_name, mode, qp) \
                  + yuv_info.yuv_name + '.' + yuv_info.suffix_type
            arg = codec_index[1] + ' ' + option.codec_dict[codec_name] % (yuv_info.url, yuv_info.width,
                                                                          yuv_info.height, yuv_info.bit_depth,
                                                                          qp, mode, output)
            print arg
            p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            info = p.communicate()
            if len(line.check_info(info)) is 0:
                line_pool.group_tag[codec_name + '_' + instance_name] = 0
                break
            decode(codec_index[3], output, yuv)
            line.add_info(info, codec_index)
            line.add_output(yuv)
            line.add_qp(qp)
            release_contain.append([output, yuv])
        if line_pool.group_tag[codec_name + '_' + instance_name] is 0:
            break
        else:
            line.get_psnr(line)
            line_pool.add_group_ele(codec_name + '_' + instance_name, line)
            database.add_data(line, codec_name + '_' + instance_name)
            for item in release_contain:
                os.remove(item[0])
                os.remove(item[1])


def setup_codec(yuv_info, database):
    line_pool = LineContain(len(option.codec))
    line_pool.set_data_type(yuv_info)
    line_pool.build_group(option.codec)
    for codec_index in option.codec:
        name = codec_index[2] + '_' + codec_index[4]
        is_find, pool = database.find_data(yuv_info, name, codec_index[5])
        if is_find:
            line_pool.group[name] = pool
        else:
            if codec_index[2] == 'HM':
                hm_execute(yuv_info, codec_index, line_pool)
            else:
                codec_execute(yuv_info, codec_index, line_pool, database)
    line_pool.check_baseline(option.codec)
    return line_pool


def clean_data_dir():
    for root, dirs, files in os.walk(option.encodeYuvPath):
        for f in files:
            apath = os.path.join(root, f)
            ext = os.path.splitext(apath)[1]
            if ext != '.png' and ext != '.csv':
                os.remove(apath)


def parse_resolution(resolution):
    resolution_dict = {'360p': 360, '480p': 480, '720p': 720, '1080p': 1080,
                       '2K': 1440, '4K': 2160, '8K': 3840, 'all': None}
    return resolution_dict[resolution]


def read_csv():
    target_yuv = parse_resolution(option.Test_data_type)
    target_yuv_contain = []
    with open(option.TestSequencePath, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0][0] == '#':
                continue
            yuv_info = yuvInfo()
            yuv_info.parse_yuv_type(row[0])
            if target_yuv is None:
                target_yuv_contain.append(yuv_info)
            elif yuv_info.height == str(target_yuv):
                target_yuv_contain.append(yuv_info)
    return target_yuv_contain


def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--plot', help='if already got data we can just plot', default=0, type=int)
    args = parser.parse_args()
    return args


def pre_setup():
    clean_data_dir()
    localtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    print('localtime=' + localtime)
    year = time.strftime('%Y', time.localtime(time.time()))
    month = time.strftime('%m', time.localtime(time.time()))
    day = time.strftime('%d', time.localtime(time.time()))
    mdhms = time.strftime('%m%d%H%M%S', time.localtime(time.time()))
    fileYear = option.proxy + year
    fileMonth = fileYear + '/' + month
    fileDay = fileMonth + '/' + day
    if not os.path.exists(fileYear):
        os.mkdir(fileYear)
        os.mkdir(fileMonth)
        os.mkdir(fileDay)
    else:
        if not os.path.exists(fileMonth):
            os.mkdir(fileMonth)
            os.mkdir(fileDay)
        else:
            if not os.path.exists(fileDay):
                os.mkdir(fileDay)
    return fileDay + '/'


def run_command():
    plot_path = pre_setup()
    time_b = time.time()
    yuv_contain = read_csv()
    case_data = CaseDate(option.calculate_data)
    database = Database(option.calculate_serialize_data)
    print "\ntest case number is %d\n" % len(yuv_contain)
    for yuv in yuv_contain:
        case = setup_codec(yuv, database)
        case.calculate()
        case_data.add_case(case, yuv)
    case_data.set_case_num()
    case_data.setup_file()
    database.serialize_date()
    ui = UI(case_data, plot_path)
    ui.show()
    elapsed = (time.time() - time_b)
    m, s = divmod(elapsed, 60)
    h, m = divmod(m, 60)
    print("time used : %d:%02d:%02d" % (h, m, s))
    clean_data_dir()


def draw_ui():
    print "we will fix this"


def main():
    args = parse_arg()
    if args.plot is 0:
        run_command()
    else:
        draw_ui()


if __name__ == '__main__':
    main()
