import numpy as np
import pandas as pd
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
                for name in [i[2] for i in option.codec]:
                    ave_bdrate = []
                    ave_fps = []
                    for case in case_:
                        ave_bdrate.append([line.bd_rate for line in case.group[name]])
                        ave_fps.append([line.average_fps for line in case.group[name]])
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
                for name in [i[2] for i in option.codec]:
                    ave_psnr = []
                    ave_bitrate = []
                    ave_bd_psnr = []
                    for case in case_:
                        ave_psnr.append([line.psnr_luam_chro for line in case.group[name]])
                        ave_bitrate.append([line.bit_rate for line in case.group[name]])
                        ave_bd_psnr.append([line.bd_psnr for line in case.group[name]])
                    encode_name.append(name)
                    encode_psnr.append(self.average_contain(ave_psnr))
                    encdoe_bitrate.append(self.average_contain(ave_bitrate))
                    encode_bdpsnr.append(self.average_list(ave_bd_psnr))
                self.bitrate_plot(encdoe_bitrate, encode_psnr, encode_name, resolution, encode_bdpsnr)

    def bd_rate_plot(self, bdrate, fps, lab, resolution):
        fig = plt.figure(figsize=[18, 10], constrained_layout=True, num=resolution)
        gs = GridSpec(2, 2, figure=fig)
        chart = fig.add_subplot(gs[0, 0])
        chart2 = fig.add_subplot(gs[1, 0])
        biao = fig.add_subplot(gs[:, 1])
        biao.set_axis_off()
        biao.set_title('%s' % resolution + 'p')
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
            if lab[i] != 'HM':
                chart.plot(fps[i], bdrate[i], '-o', label=lab[i])
            chart2.plot(range(xrow), bdrate[i], '-x', label=lab[i])
        chart.legend()
        for line in chart2.xaxis.get_ticklabels():
            line.set_rotation(45)
        chart2.yaxis.set_major_locator(MultipleLocator(10))
        chart2.yaxis.set_major_formatter(FuncFormatter(persent))
        chart2.set_xticks([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        if 'HM' in [code[2] for code in option.codec]:
            baseline = 'HM'
        else:
            baseline = 'svt'
        rowlabel = ['vs %s mode 0' % baseline, 'vs %s mode 1' % baseline, 'vs %s mode 2' % baseline,
                    'vs %s mode 3' % baseline,
                    'vs %s mode 4' % baseline, 'vs %s mode 5' % baseline, 'vs %s mode 6' % baseline,
                    'vs %s mode 7' % baseline,
                    'vs %s mode 8' % baseline, 'vs %s mode 9' % baseline]
        chart2.set_xticklabels(rowlabel)
        chart2.legend()
        trans_bdrate = self.trans_list(self.fix_arr(bdrate))
        biao.table(cellText=trans_bdrate, colLabels=lab, rowLabels=rowlabel, loc='center',
                   colWidths=[0.1 for i in range(len(lab))])
        plt.pause(10)
        info = ''
        for code in option.codec:
            info += '_' + code[4] + '_'
        fig.savefig(option.plot_path + '_' + str(resolution) + '_' + info + '_BDrate')

    def fix_arr(self, bdrate):
        max = 0
        for rate in bdrate:
            if max < len(rate):
                max = len(rate)
        for rate in bdrate:
            if len(rate) < max:
                for i in range(max - len(rate)):
                    rate.append(rate[-1])
        return bdrate

    def bitrate_plot(self, encdoe_bitrate, encode_psnr, encode_name, resolution, encode_bdpsnr):
        fig = plt.figure(figsize=[16, 8], constrained_layout=True)
        gs = GridSpec(1, 3, figure=fig)
        chart = fig.add_subplot(gs[0, :2])
        biao = fig.add_subplot(gs[0, 2])
        biao.set_axis_off()
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
        rowlabel = ['mode 0', 'mode 1', 'mode 2', 'mode 3', 'mode 4', 'mode 5', 'mode 6', 'mode 7', 'mode 8', 'mode 9']
        biao.table(cellText=trans_psnr, colLabels=encode_name, rowLabels=rowlabel, loc='center',
                   colWidths=[0.1 for i in range(len(encode_name))])
        plt.pause(10)
        info = ''
        for code in option.codec:
            info += '_' + code[4]
        fig.savefig(option.plot_path + '_' + str(resolution) + info + '_bit_rate')

    def show(self):
        self.bd_data_choose()
        self.bitrate_data_choos()
