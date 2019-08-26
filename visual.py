#!/usr/bin/env python

"""
Visually show various metrics between two YCbCr sequences
using matplotlib
"""

import argparse
import time
import os
import xlrd
from Data_struct import Line, LineContain, CaseDate

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FuncFormatter
from ycbcr import YCbCr
from matplotlib.gridspec import GridSpec
import bjontegaard_metric as BD
import OptionDictionary as config

bdrate_contain = []
fps_contain = []


def create_title_string(title, subtitle):
    """
    Helper function to generate a nice looking
    title string
    """
    return "{} {}\n{}".format(
        os.path.basename(title),
        'VS.',
        " ".join([os.path.basename(i) for i in subtitle]))


def plot_psnr(arg):
    """
    PSNR
    """
    t, st = vars(arg)['filename'], vars(arg)['filename_diff']
    for f in st:
        vars(arg)['filename_diff'] = f
        yuv = YCbCr(**vars(arg))

        psnr = [p[3] for p in yuv.psnr()]

        N = len(psnr[:-2])
        ind = np.arange(N)  # the x locations for the groups

        # To get a uniq identifier
        plt.plot(ind, psnr[:-2], 'o-', label=f[-10:-8])

        del yuv

    plt.legend()
    plt.title(create_title_string(t, st))
    plt.ylabel('weighted dB')
    plt.xlabel('frame')
    plt.grid(True)
    plt.show()


def sort_point(ind, point):
    contain = []
    for i in range(len(ind)):
        contain.append([ind[i], point[i]])

    def takefirst(ele):
        return ele[0]

    contain.sort(key=takefirst)
    ind = []
    point = []
    for i in range(len(contain)):
        ind.append(contain[i][0])
        point.append(contain[i][1])
    return [ind, point]


def calculate_hm_distance(BD_contain):
    BDRate_contain = []
    BD_PSNR_contain = []
    mode_sum = len(config.svt_mode)
    for i in range(1, len(BD_contain)):
        BDRate = BD.BD_RATE(BD_contain[0][0], BD_contain[0][1], BD_contain[i][0], BD_contain[i][1])
        BD_PSNR = BD.BD_PSNR(BD_contain[0][0], BD_contain[0][1], BD_contain[i][0], BD_contain[i][1])
        BDRate_contain.append(BDRate)
        BD_PSNR_contain.append(BD_PSNR)
    return BDRate_contain, BD_PSNR_contain


def calculate_hm_average(BD_contain):
    BDRate_contain = []
    BD_PSNR_contain = []
    mode_sum = len(config.svt_mode)
    for i in range(1, len(BD_contain)):
        BDRate = BD.BD_RATE_Average(BD_contain[0][0], BD_contain[0][1], BD_contain[i][0], BD_contain[i][1])
        BD_PSNR = BD.BD_PSNR_Average(BD_contain[0][0], BD_contain[0][1], BD_contain[i][0], BD_contain[i][1])
        BDRate_contain.append(BDRate)
        BD_PSNR_contain.append(BD_PSNR)
    return BDRate_contain, BD_PSNR_contain


def calculate_distance(BD_contain):
    celltext = []
    rowname = []
    tag = 0
    while tag < len(BD_contain):
        x265_rate = BD.BD_RATE(BD_contain[tag][0], BD_contain[tag][1], BD_contain[tag + 1][0], BD_contain[tag + 1][1])
        svt_rate = BD.BD_RATE(BD_contain[tag][0], BD_contain[tag][1], BD_contain[tag + 2][0], BD_contain[tag + 2][1])
        x265_psnr = BD.BD_PSNR(BD_contain[tag][0], BD_contain[tag][1], BD_contain[tag + 1][0], BD_contain[tag + 1][1])
        svt_psnr = BD.BD_PSNR(BD_contain[tag][0], BD_contain[tag][1], BD_contain[tag + 2][0], BD_contain[tag + 2][1])
        rowname.append(BD_contain[tag][3][0].split('/')[-1] + '_' + BD_contain[tag][2])
        rowname.append(BD_contain[tag + 1][3][0].split('/')[-1] + '_' + BD_contain[tag + 1][2])
        rowname.append(BD_contain[tag + 2][3][0].split('/')[-1] + '_' + BD_contain[tag + 2][2])
        celltext.append(['HM base line', 'HM base line'])
        celltext.append([x265_rate, x265_psnr])
        celltext.append([svt_rate, svt_psnr])
        tag += 3
    return celltext, rowname


def calculate_average(BD_contain):
    celltext = []
    rowname = []
    tag = 0
    while tag < len(config.svt_mode):
        # HM_rate = BD.BD_RATE_Average(BD_contain[0][0],BD_contain[0][1])
        HM_psnr = BD.BD_PSNR_Average(BD_contain[0][0], BD_contain[0][1])
        # x265_rate = BD.BD_RATE_Average(BD_contain[tag+1][0], BD_contain[tag+1][1])
        # svt_rate = BD.BD_RATE_Average(BD_contain[tag+2][0], BD_contain[tag+2][1])
        x265_psnr = BD.BD_PSNR_Average(BD_contain[tag + 1][0], BD_contain[tag + 1][1])
        svt_psnr = BD.BD_PSNR_Average(BD_contain[tag + 11][0], BD_contain[tag + 11][1])
        rowname.append(BD_contain[0][3][0].split('/')[-1] + '_' + 'mode_%d' % tag)
        celltext.append([HM_psnr, x265_psnr, svt_psnr])
        tag += 1
    return celltext, rowname


def get_psnr(line):
    yuv = YCbCr(filename=line.input_url, filename_diff=line.output, width=line.width,
                height=line.height, yuv_format_in=line.type, bitdepth=line.bit_depth)
    for infile in range(line.input_url):
        for diff_file in range(line.output):
            psnr_frame = [p for p in yuv.psnr_all(diff_file, infile)]
            line.add_psnr(psnr_frame[-1])
        line.sort()
        line.set_average_fps()
        line.set_bd_psnr(BD.BD_PSNR_Average(line.bit_rate, line.psnr))


def get_bd_rate(baseline, line):
    return BD.BD_RATE(baseline.bit_rate, baseline.psnr, line.bit_rate, line.psnr)


def get_psnr_value(contain, bits_psnr=0):
    BD_contain = []
    for i in range(len(contain)):
        yuv = YCbCr(filename=contain[i][0], filename_diff=contain[i][1], width=int(contain[i][5]),
                    height=int(contain[i][6]), yuv_format_in=contain[i][7], bitdepth=contain[i][4])
        for infile in range(len(contain[i][0])):
            point = []
            xax = []
            for diff_file in range(len(contain[i][1])):
                temp = [p for p in yuv.psnr_all(diff_file, infile)]
                ind = np.arange(len(temp))
                frame = [frame_order[0] for frame_order in temp]
                point.append(temp[-1])
                xax.append(contain[i][2][diff_file])
                # frames_psnr.plot(ind[0:-1], frame[0:-1], 'o-', label=contain[i][3]+'_'+str(contain[i][2][diff_file]))
            temp_sort = sort_point(xax, point)
            db_psnr_contain = []
            for db_psnr in temp_sort[1]:
                db_psnr_contain.append(db_psnr[-1])
            if bits_psnr is 0:
                BD_contain.append(
                    [temp_sort[0], db_psnr_contain, contain[i][3], contain[i][0], temp_sort[1], contain[i][8]])
            else:
                bits_psnr.plot(temp_sort[0], db_psnr_contain, 'o-', label=contain[i][3])
                BD_contain.append(
                    [temp_sort[0], db_psnr_contain, contain[i][3], contain[i][0], temp_sort[1], contain[i][8]])
    return BD_contain


def calculate_JustOne_distance(Baseline, svt_diff):
    return BD.BD_RATE(Baseline[0], Baseline[1], svt_diff[0], svt_diff[1])


def calculate_svt_distance(BD_contain):
    BDRate_Container = []
    Baseline = BD_contain[0]
    mode_sum = len(config.svt_mode)
    for svt_diff in range(len(config.svt_Qp)):
        for mode_num in range(mode_sum):
            BDRate = calculate_JustOne_distance(Baseline, BD_contain[svt_diff * mode_sum + mode_num])
            BDRate_Container.append(BDRate)
    return BDRate_Container


def get_Xaxis_value():
    mode_sum = len(config.svt_mode)
    compare_sum = len(config.svt_Qp)
    Xaxis_name = []
    for j in range(mode_sum):
        name = 'M%d vs %s_M%d' % (j, config.svt_Qp[0][2], j)
        Xaxis_name.append(name)
    return Xaxis_name


def get_celltext(BDRate_Container):
    mode_sum = len(config.svt_mode)
    codec_sum = len(config.svt_Qp)
    BDRate_table = []
    for j in range(mode_sum):
        row_value = []
        for i in range(codec_sum):
            row_value.append(BDRate_Container[i * mode_sum + j])
        BDRate_table.append(row_value)
    return BDRate_table


def get_collable():
    collable = []
    for i in config.svt_Qp:
        collable.append(i[2])
    return collable


def average_fps(fps):
    sum = 0
    for i in fps:
        sum += i
    return sum / len(fps)


def average_psnr(psnr):
    sum = psnr[0]
    for p in psnr[1:len(psnr)]:
        sum = [sum[i] + p[i] for i in range(0, len(p))]
    return [sum[i] / len(psnr) for i in range(0, len(sum))]


def get_fps(BD_contain):
    x265, svt = [], []
    mode_sum = len(config.svt_mode)
    for i in range(1, 1 + mode_sum):
        x265.append(average_fps(BD_contain[i][5]))
        svt.append(average_fps(BD_contain[i + mode_sum][5]))
    return x265, svt


def get_fps_svt(BD_contain):
    mode_sum = len(config.svt_mode)
    codec_sum = len(config.svt_Qp)
    fps_svt = [None] * codec_sum
    for i in range(codec_sum):
        fps_svt[i] = []
    for i in range(mode_sum):
        for j in range(codec_sum):
            fps_svt[j].append(average_fps(BD_contain[mode_sum * j + i][5]))
    return fps_svt


def BDBR_average(contain):
    case_num = len(contain)
    sum = contain[0]
    for case in contain[1:case_num]:
        sum = [sum[i] + case[i] for i in range(0, len(case))]
    return [sum[i] / case_num for i in range(0, len(sum))]


def final_plot_hm():
    fig = plt.figure(figsize=[16, 6], constrained_layout=True)
    gs = GridSpec(1, 2, figure=fig)
    DBDR_plot = fig.add_subplot(gs[0, 0])
    DBDR = fig.add_subplot(gs[0, 1])
    DBDR.set_axis_off()
    DBDR_plot.set_ylabel('BDRate base HM')
    DBDR_plot.set_xlabel('Speed(fps)')
    DBDR_plot.grid(True)
    DBDR_plot.set_xlim(0, None, True, True)
    DBDR_plot.set_ylim(0, 100, True, True)

    def persent(temp, position):
        return '%1.1f' % (temp) + '%'

    DBDR_plot.yaxis.set_major_locator(MultipleLocator(10))
    DBDR_plot.yaxis.set_major_formatter(FuncFormatter(persent))
    bdbr = BDBR_average(bdrate_contain)
    fps = BDBR_average(fps_contain)
    DBDR_plot.plot(fps[:len(config.svt_mode)], bdbr[:len(config.svt_mode)], 'o-', label='x265')
    DBDR_plot.plot(fps[len(config.svt_mode):], bdbr[len(config.svt_mode):], 'v-', label='svt')
    celltext = get_celltext(bdbr)
    rowname = get_Xaxis_value()
    DBDR.table(cellText=celltext, colLabels=['x265', 'svt'], rowLabels=rowname, loc='center', colWidths=[0.2, 0.2])
    DBDR_plot.legend()
    plt.show()


def plot_psnr_svt(contain, case_count):
    fig = plt.figure(figsize=[16, 10])
    gs = GridSpec(2, 2, figure=fig)
    plt.suptitle('PSNR BDRate')
    chart = fig.add_subplot(gs[0, 0])
    table = fig.add_subplot(gs[0, 1])
    chart2 = fig.add_subplot(gs[1, 0])
    table.set_axis_off()
    chart.set_title('BDRate vs Mode')
    chart.set_xlabel('Speed(fps)')
    chart.set_ylabel('BDRate')
    chart.set_xlim(0, None, True, True)
    chart.set_ylim(-20, 100, True, False)
    chart2.set_ylim(-20, 100, True, False)

    def persent(temp, position):
        return '%1.1f' % (temp) + '%'

    chart.yaxis.set_major_locator(MultipleLocator(10))
    chart.yaxis.set_major_formatter(FuncFormatter(persent))
    # chart2.xaxis.set_major_locator(MultipleLocator(1))

    BD_contain = get_psnr_value(contain)
    BDRate_Container = calculate_svt_distance(BD_contain)
    celltext = get_celltext(BDRate_Container)
    Xaxis_name = get_Xaxis_value()
    collable = get_collable()
    table.table(cellText=celltext, colLabels=collable, rowLabels=Xaxis_name, loc='center', colWidths=[0.2, 0.2])
    mode_sum = len(config.svt_mode)
    codec_sum = len(config.svt_Qp)
    svt_fps = get_fps_svt(BD_contain)
    for codec in range(codec_sum):
        chart.plot(svt_fps[codec], BDRate_Container[codec * mode_sum:(codec + 1) * mode_sum], 'o-',
                   label=config.svt_Qp[codec][2])
        chart2.plot(range(mode_sum), BDRate_Container[codec * mode_sum:(codec + 1) * mode_sum], 'o-',
                    label=config.svt_Qp[codec][2])
    for line in chart2.xaxis.get_ticklabels():
        line.set_rotation(45)

    chart2.yaxis.set_major_locator(MultipleLocator(10))
    chart2.yaxis.set_major_formatter(FuncFormatter(persent))
    chart2.set_xticks([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    chart2.set_xticklabels(Xaxis_name)
    chart2.legend()
    chart2.grid(True)
    chart.legend()
    chart.grid(True)
    # TODO we should store our data , to get average number
    bdrate_contain.append(BDRate_Container)
    fps_contain.append(svt_fps)
    if case_count is 0:
        plt.show()
    else:
        plt.pause(10)


def plot_psnr_frames(contain, case_count):
    """
    PSNR, all planes
    """
    fig = plt.figure(figsize=[16, 10], constrained_layout=True)
    gs = GridSpec(2, 2, figure=fig)
    plt.suptitle('yuv Quality plot')
    DBDR_plot = fig.add_subplot(gs[0, 0])
    DBDR = fig.add_subplot(gs[0, 1])
    DBDR.set_axis_off()

    DBDR_plot.set_ylabel('BDRate base HM')
    DBDR_plot.set_xlabel('Speed(fps)')
    DBDR_plot.grid(True)
    DBDR_plot.set_xlim(0, None, True, True)
    DBDR_plot.set_ylim(0, 100, True, True)

    def persent(temp, position):
        return '%1.1f' % (temp) + '%'

    DBDR_plot.yaxis.set_major_locator(MultipleLocator(10))
    DBDR_plot.yaxis.set_major_formatter(FuncFormatter(persent))

    bits_psnr = fig.add_subplot(gs[1, 0])
    DBDR_for_each = fig.add_subplot(gs[1, 1])
    DBDR_for_each.set_title('BD_PSNR')
    DBDR_for_each.set_axis_off()
    bits_psnr.set_title('Psnr vs Bitrate')
    bits_psnr.set_xlabel('bitrate')
    bits_psnr.set_ylabel('psnr')

    BD_contain = get_psnr_value(contain, bits_psnr)
    BDRate_contain, BD_PSNR_contain = calculate_hm_distance(BD_contain)
    x265_fps, svt_fps = get_fps(BD_contain)
    DBDR_plot.plot(x265_fps, BDRate_contain[:len(config.svt_mode)], 'o-', label=contain[len(config.svt_mode)][3])
    DBDR_plot.plot(svt_fps, BDRate_contain[len(config.svt_mode):], 'v-', label=contain[-1][3])
    celltext = get_celltext(BDRate_contain)
    rowname = get_Xaxis_value()
    DBDR.table(cellText=celltext, colLabels=['x265', 'svt'], rowLabels=rowname, loc='center', colWidths=[0.2, 0.2])
    text, name = calculate_average(BD_contain)
    DBDR_for_each.table(cellText=text, colLabels=['HM', 'x265', 'svt'], rowLabels=name, loc='center')
    # bits_psnr.plot(BDRate_contain[0][0],BDRate_contain[0][1], 'o-', lable='HM')
    # bits_psnr.plot(average_psnr(BDRate_contain[1:11][0]),average_psnr(BDRate_contain[1:11][1]))
    # bits_psnr.plot()
    # bits_psnr.legend()
    bits_psnr.grid(True)
    DBDR_plot.legend()
    bdrate_contain.append(BDRate_contain)
    fps_contain.append(x265_fps + svt_fps)
    if case_count is 0:
        plt.pause(10)
        final_plot_hm()
    else:
        plt.pause(10)


def find_all_yuv_fromdir(arg, inputfile, grouptag):
    path = arg.inputpath
    dirs = os.listdir(path)
    Originalyuvpath = []
    for file in dirs:
        if file == inputfile:
            Originalyuvpath.append(os.path.join(path, file))
            break
    encodeyuvpath = []
    for tag in range(len(grouptag)):
        for file in dirs:
            if file == grouptag[tag]:
                encodeyuvpath.append(os.path.join(path, file))
                break
    return [Originalyuvpath, encodeyuvpath, arg.Bit_rate, inputfile]


def find_all_yuv(arg, inputfile, grouptag):
    workbook = xlrd.open_workbook(arg.inputpath)
    worksheet = workbook.sheet_by_index(0)
    y = 0
    titlename = {}
    while y < worksheet.ncols:
        titlename[str(worksheet.cell(0, y).value)] = y
        y += 1
    order = 0
    while order < worksheet.nrows:
        if worksheet.cell(order, 0).value == inputfile:
            break
        order = order + 1
    Originalyuvpath = [str(worksheet.cell(order, 3).value)]
    encodeyuvpath = []
    encodeyuvbitrate = []
    encodeyuvbitdepth = 8
    width = 1
    height = 1
    type = 'YU12'
    linetag = 'haha'
    order = 0
    while order < worksheet.nrows:
        if worksheet.cell(order, 7).value == inputfile and worksheet.cell(order, 8).value == grouptag:
            encodeyuvpath.append(str(worksheet.cell(order, 3).value))
            encodeyuvbitrate.append(worksheet.cell(order, 6).value)
            linetag = str(worksheet.cell(order, 8).value)
            # linetag = str(worksheet.cell(order, 8).value + '_' + worksheet.cell(order, 7).value)
            encodeyuvbitdepth = int(worksheet.cell(order, 5).value)
            width = int(worksheet.cell(order, 1).value)
            height = int(worksheet.cell(order, 2).value)
            type = str(worksheet.cell(order, 4).value)
        order = order + 1
    return [Originalyuvpath, encodeyuvpath, encodeyuvbitrate, linetag, encodeyuvbitdepth, width, height, type]


def main():
    args = parse_args()
    contain = []
    for i in range(len(args.input_test)):
        compare_test = find_all_yuv(args, args.input_test[i], args.grouptag[i])
        contain.append(compare_test)
    t1 = time.clock()
    plot_psnr_frames(contain)
    t2 = time.clock()
    print "\nTime: ", round(t2 - t1, 4)


def parse_args():
    parser = argparse.ArgumentParser()
    # parser.add_argument('-I', '--filename', type=str, help='filename', nargs='+')
    # we need modify this to read excel path
    parser.add_argument('-I', '--inputpath', type=str, help='the excel configure file path', nargs='?')
    # parser.add_argument('-g', '--testgroup', type=int, help='testgroup_number',  nargs='?')
    parser.add_argument('-P', '--input_test', type=str,
                        help='the Original yuv file name, you can put plenty,and separate by dot', nargs='+',
                        required=False)
    parser.add_argument('-po', '--compare_test', type=str, help='compare_test_plan', action='append', required=False)
    parser.add_argument('-W', '--width', type=int, required=False, help='width')
    parser.add_argument('-H', '--height', type=int, required=False, help='height')
    parser.add_argument('-C', '--yuv_format_in', choices=['IYUV', 'UYVY', 'YV12', 'YVYU', 'YUY2', '422'],
                        required=False, help='type')
    parser.add_argument('-M', '--Bit_rate', type=int, help='bitrate with compare yuv', nargs='+')
    parser.add_argument('-G', '--grouptag', type=str, help='different transcoding yuv', nargs='+')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
