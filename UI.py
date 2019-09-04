import numpy as np
import pandas as pd
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MultipleLocator, FuncFormatter
import OptionDictionary as option


class UI:
    def __init__(self, data):
        self.data = data
        self.case_num = data.case_num
        self.encode_num = len(option.codec)
        self.bd_fps = []
        self.bd_rate = []
        self.bd_label = []

    def average_list(self, arr):
        sum = 0
        result = []
        for col in range(len(arr[0])):
            for row in range(len(arr)):
                sum += arr[row][col]
            result.append(sum / len(arr))
            sum = 0
        return result

    def average_contain(self, contain):
        result = []
        for mode in range(len(contain[0])):
            line_mode = [line[mode] for line in contain]
            result.append(self.average_list(line_mode))
        return result

    def trans_list(self, arr):
        trans = []
        for col in range(len(arr[0])):
            trans.append([row[col] for row in arr])
        return trans

    def bd_data_choose(self):
        for resolution, case_ in self.data.case_group.items():
            encdoe_bdrate = []
            encode_fps = []
            encode_name = []
            if len(case_) > 0:
                for name in [[i[2], i[4]] for i in option.codec]:
                    ave_bdrate = []
                    ave_fps = []
                    for case in case_:
                        ave_bdrate.append([line.bd_rate for line in case.group[name[0] + '_' + name[1]]])
                        ave_fps.append([line.average_fps for line in case.group[name[0] + '_' + name[1]]])
                    encode_name.append(name)
                    encdoe_bdrate.append(self.average_list(ave_bdrate))
                    encode_fps.append(self.average_list(ave_fps))
                self.bd_rate_plot(encdoe_bdrate, encode_fps, encode_name, resolution)

    def bitrate_data_choos(self):
        for resolution, case_ in self.data.case_group.items():
            if len(case_) > 0:
                encdoe_bitrate = []
                encode_psnr = []
                encode_name = []
                encode_bdpsnr = []
                for name, tag in [[i[2], i[4]] for i in option.codec]:
                    ave_psnr = []
                    ave_bitrate = []
                    ave_bd_psnr = []
                    for case in case_:
                        ave_psnr.append([line.psnr_luam_chro for line in case.group[name + '_' + tag]])
                        ave_bitrate.append([line.bit_rate for line in case.group[name + '_' + tag]])
                        ave_bd_psnr.append([line.bd_psnr for line in case.group[name + '_' + tag]])
                    encode_name.append(name + '_' + tag)
                    encode_psnr.append(self.average_contain(ave_psnr))
                    encdoe_bitrate.append(self.average_contain(ave_bitrate))
                    encode_bdpsnr.append(self.average_list(ave_bd_psnr))
                self.bitrate_plot(encdoe_bitrate, encode_psnr, encode_name, resolution, encode_bdpsnr)

    def bd_rate_plot(self, bdrate, fps, lab, resolution):
        fig = plt.figure(figsize=[18, 10])
        gs = GridSpec(2, 2)
        chart = fig.add_subplot(gs[0, 0])
        chart2 = fig.add_subplot(gs[1, 0])
        biao = fig.add_subplot(gs[:, 1])
        biao.set_axis_off()
        biao.set_title('%s' % resolution + 'p   '+'BDrate')
        chart.set_xlabel('Speed(fps)')
        chart.set_ylabel('BDRate')
        chart.grid(True)
        chart.set_xlim(0, None, True, True)
        chart.set_ylim(-100, 100, True, True)
        chart.set_title('%s' % resolution + 'p')
        chart2.set_xlabel('Mode')
        chart2.set_ylabel('BDRate')
        chart2.grid(True)
        chart2.set_xlim(0, None, True, True)
        chart2.set_ylim(-100, 100, True, True)
        chart2.set_title('%s' % resolution + 'p')

        def persent(temp, position):
            return '%1.1f' % (temp) + '%'

        chart.yaxis.set_major_locator(MultipleLocator(10))
        chart.yaxis.set_major_formatter(FuncFormatter(persent))
        for i in range(len(bdrate)):
            xrow = len(bdrate[i])
            if lab[i][0] != 'HM':
                chart.plot(fps[i], bdrate[i], '-o', label=lab[i][0] + '_' + lab[i][1])
            chart2.plot(range(xrow), bdrate[i], '-x', label=lab[i][0] + '_' + lab[i][1])
        chart.legend()
        for line in chart2.xaxis.get_ticklabels():
            line.set_rotation(45)
        chart2.yaxis.set_major_locator(MultipleLocator(10))
        chart2.yaxis.set_major_formatter(FuncFormatter(persent))
        chart2.set_xticks(range(self.max_len(bdrate)))
        if 'HM' in [code[2] for code in option.codec]:
            baseline = 'HM'
        else:
            baseline = 'svt'
        rowlabel = self.label_len(bdrate, 'bd', baseline)
        chart2.set_xticklabels(rowlabel)
        chart2.legend()
        trans_bdrate = self.trans_list(self.fix_arr(bdrate))
        biao.table(cellText=trans_bdrate, colLabels=[col[0] + '_' + col[1] for col in lab], rowLabels=rowlabel,
                   loc='center',
                   colWidths=[0.2 for i in range(len(lab))])
        #plt.pause(10)
        info = ''
        for code in option.codec:
            info += '_' + code[4] + '_'
        fig.savefig(option.plot_path + '_' + str(resolution) + '_' + info + '_BDrate')

    def max_len(self, bd):
        max = 10
        for rate in bd:
            if max < len(rate):
                max = len(rate)
        return max

    def fix_arr(self, bdrate):
        max = self.max_len(bdrate)
        for rate in bdrate:
            if len(rate) < max:
                for i in range(max - len(rate)):
                    rate.append('0')
        return bdrate

    def label_len(self, bdrate, tag, baseline=None):
        max = self.max_len(bdrate)
        row_label = []
        for i in range(max):
            if tag == 'bd':
                row_label.append('vs %s mode %s' % (baseline, i))
            elif tag == 'bit':
                row_label.append('mode %s' % i)
        return row_label

    def bitrate_plot(self, encdoe_bitrate, encode_psnr, encode_name, resolution, encode_bdpsnr):
        fig = plt.figure(figsize=[16, 8])
        gs = GridSpec(1, 3)
        chart = fig.add_subplot(gs[0, :2])
        biao = fig.add_subplot(gs[0, 2])
        biao.set_axis_off()
        biao.set_title('%s' % resolution + 'p   '+'BD-PSNR')
        chart.set_title('%s' % resolution + 'p')
        chart.set_xlabel('bit_rate')
        chart.set_ylabel('PSNR')
        chart.grid(True)
        for encode in range(len(encode_name)):
            for mode in range(len(encdoe_bitrate[encode])):
                chart.plot(encdoe_bitrate[encode][mode], encode_psnr[encode][mode], '-o',
                           label=encode_name[encode] + '_' + str(mode))
        chart.legend(loc='right')
        trans_psnr = self.trans_list(self.fix_arr(encode_bdpsnr))
        rowlabel = self.label_len(encode_bdpsnr, 'bit')
        biao.table(cellText=trans_psnr, colLabels=encode_name, rowLabels=rowlabel, loc='center',
                   colWidths=[0.3 for i in range(len(encode_name))])
        #plt.pause(10)
        info = ''
        for code in option.codec:
            info += '_' + code[4]
        fig.savefig(option.plot_path + '_' + str(resolution) + info + '_bit_rate')

    def show(self):
        self.bd_data_choose()
        self.bitrate_data_choos()
