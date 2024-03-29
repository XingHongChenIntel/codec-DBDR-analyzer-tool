import numpy as np
import pandas as pd
import copy
import os
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MultipleLocator, FuncFormatter
import OptionDictionary as option


class UI:
    def __init__(self, data, plot_path):
        self.data = data
        self.case_num = data.case_num
        self.encode_num = len(option.codec)
        self.bd_fps = []
        self.bd_rate = []
        self.bd_label = []
        self.plot_path = plot_path

    def average_list(self, arr):
        sum = 0
        result = []
        for col in range(len(arr[0])):
            for row in range(len(arr)):
                sum += arr[row][col]
            result.append(round(sum / len(arr), 2))
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
                        ave_psnr.append([line.psnr for line in case.group[name + '_' + tag]])
                        ave_bitrate.append([line.bit_rate for line in case.group[name + '_' + tag]])
                        ave_bd_psnr.append([line.bd_psnr for line in case.group[name + '_' + tag]])
                    encode_name.append(name + '_' + tag)
                    encode_psnr.append(self.average_contain(ave_psnr))
                    encdoe_bitrate.append(self.average_contain(ave_bitrate))
                    encode_bdpsnr.append(self.average_list(ave_bd_psnr))
                self.bitrate_plot(encdoe_bitrate, encode_psnr, encode_name, resolution, encode_bdpsnr)

    def all_detail(self):
        for resolution, case_ in self.data.case_group.items():
            if len(case_) > 0:
                if not os.path.exists(self.plot_path+str(resolution)):
                    os.mkdir(self.plot_path+resolution)
                bd_psnr, bd_rate, com_psnr, com_bitrate, com_avepsnr = [], [], [], [], []
                table_name, col_name, legend_name = [], [], []
                for case in case_:
                    psnr, bitrate, ave_psnr, label, ff = [], [], [], [], []
                    for name, tag in [[i[2], i[4]] for i in option.codec]:
                        # 0 is mode number.
                        line = case.group[name + '_' + tag][0]
                        psnr.append(line.psnr)
                        bitrate.append(line.bit_rate)
                        ave_psnr.append([line.bd_psnr])
                        ff.append(line.bd_psnr)
                        label.append(tag+'_'+line.yuv_info.yuv_name)
                        if line is not case.baseline:
                            bd_psnr.append([line.BD_psnr_luam, line.BD_psnr_charm_cb, line.BD_psnr_charm_cr,
                                            line.BD_psnr])
                            bd_rate.append([line.bd_rate_luma, line.bd_rate_charm_cb, line.bd_rate_charm_cr,
                                            str(round(line.bd_rate, 2)) + '%'])
                            table_name.append(line.yuv_info.yuv_name+'_'+tag)
                    self.detail_plot(psnr, bitrate, ave_psnr, label, resolution, [line.yuv_info.yuv_name])
                    com_psnr.extend(psnr)
                    com_bitrate.extend(bitrate)
                    com_avepsnr.append(ff)
                    col_name.append(line.yuv_info.yuv_name)
                    legend_name.extend(label)
                row_name = []
                for name, tag in [[i[2], i[4]] for i in option.codec]:
                        row_name.append(name+'_'+tag)
                self.detail_plot_com(com_psnr, com_bitrate, com_avepsnr, legend_name,
                                 resolution, col_name, row_name)
                if len(bd_psnr) and len(bd_rate):
                    self.BD_table(bd_psnr, table_name, resolution, 'psnr')
                    self.BD_table(bd_rate, table_name, resolution, 'rate')
                else:
                    print 'warning: there is only one encode, can not show BD table!'

    def BD_table(self, psnr, row, resolution, title):
        fig = plt.figure(figsize=[16, 8])
        gs = GridSpec(1, 1)
        biao = fig.add_subplot(gs[0, 0])
        biao.set_axis_off()
        biao.set_title('%s' % resolution + 'p   ' + 'BD_'+title)
        biao.table(cellText=psnr, colLabels=['Y_'+title, 'U_'+title, 'V_'+title, 'YUV_'+title],
                   rowLabels=row, loc=0, colWidths=[0.2, 0.2, 0.2, 0.2],edges='horizontal')
        fig.savefig(self.plot_path + str(resolution) + '/' +resolution+ 'BD-'+title)

    def detail_plot(self, psnr, bitrate, ave_psnr, name, resolution, case_name):
        fig = plt.figure(figsize=[16, 8])
        gs = GridSpec(2, 5)
        chart = fig.add_subplot(gs[0, :3])
        biao = fig.add_subplot(gs[1, 3:])
        biao.set_axis_off()
        biao.set_title('%s' % resolution + 'p   ' + 'BD-PSNR')
        chart.set_title('%s' % resolution + 'p')
        chart.set_xlabel('bit_rate')
        chart.set_ylabel('PSNR')
        chart.grid(True)
        for num in range(len(psnr)):
            chart.plot(bitrate[num], psnr[num], '-o', label=name[num])
        chart.legend(loc=0)
        biao.table(cellText=ave_psnr, colLabels=case_name, rowLabels=name, loc=0,
                   colWidths=[0.4 for i in range(len(case_name))],edges='horizontal')
        fig.savefig(self.plot_path + str(resolution) + '/' + case_name[0])

    def detail_plot_com(self, psnr, bitrate, ave_psnr, name, resolution, row_name, col_name):
        fig = plt.figure(figsize=[16, 8])
        gs = GridSpec(2, 5)
        chart = fig.add_subplot(gs[0, :3])
        biao = fig.add_subplot(gs[1, 3:])
        biao.set_axis_off()
        biao.set_title('%s' % resolution + 'p   ' + 'BD-PSNR')
        chart.set_title('%s' % resolution + 'p')
        chart.set_xlabel('bit_rate')
        chart.set_ylabel('PSNR')
        chart.grid(True)
        for num in range(len(psnr)):
            chart.plot(bitrate[num], psnr[num], '-o', label=name[num])
        #chart.legend(loc=0)
        biao.table(cellText=ave_psnr, colLabels=col_name, rowLabels=row_name, loc=0,
                   colWidths=[0.4 for i in range(len(col_name))],edges='horizontal')
        fig.savefig(self.plot_path + str(resolution) + '/' + 'combo_plot')

    def bd_rate_plot(self, bdrate, fps, lab, resolution):
        fig = plt.figure(figsize=[16, 8])
        gs = GridSpec(1, 5)
        # chart = fig.add_subplot(gs[0, 0:3])
        chart2 = fig.add_subplot(gs[0, 0:3])
        biao = fig.add_subplot(gs[:, 3:5])
        biao.set_axis_off()
        biao.set_title('%s' % resolution + 'p   ' + 'BDrate')
        # chart.set_xlabel('Speed(fps)')
        # chart.set_ylabel('BDRate')
        # chart.grid(True)
        # chart.set_xlim(0, None, True, True)
        # chart.set_ylim(-100, 100, True, True)
        # chart.set_title('%s' % resolution + 'p')
        chart2.set_xlabel('Mode')
        chart2.set_ylabel('BDRate')
        chart2.grid(True)
        chart2.set_xlim(0, None, True, True)
        chart2.set_ylim(-20, 100, True, True)
        chart2.set_title('%s' % resolution + 'p')

        def persent(temp, position):
            return '%1.1f' % (temp) + '%'

        # chart.yaxis.set_major_locator(MultipleLocator(10))
        # chart.yaxis.set_major_formatter(FuncFormatter(persent))
        for i in range(len(bdrate)):
            xrow = len(bdrate[i])
            # if lab[i][0] != 'HM':
            #     chart.plot(fps[i], bdrate[i], '-o', label=lab[i][0] + '_' + lab[i][1])
            chart2.plot(option.mode[0:xrow], bdrate[i], '-x', label=lab[i][0] + '_' + lab[i][1])
        # chart.legend()
        for line in chart2.xaxis.get_ticklabels():
            line.set_rotation(45)
        chart2.yaxis.set_major_locator(MultipleLocator(10))
        chart2.yaxis.set_major_formatter(FuncFormatter(persent))
        chart2.set_xticks(range(self.max_len(bdrate)))
        for codec in option.codec:
            if codec[6] == 'baseline':
                baseline = codec[2]
        rowlabel = self.label_len(bdrate, 'bd', baseline)
        chart2.set_xticklabels(rowlabel)
        chart2.legend(loc=0)
        trans_bdrate = self.trans_list(self.fix_arr(bdrate))
        biao.table(cellText=trans_bdrate, colLabels=[col[0] + '_' + col[1] for col in lab], rowLabels=rowlabel,
                   loc=0, edges='horizontal',
                   colWidths=[0.2 for i in range(len(lab))])
        info = ''
        for code in option.codec:
            info += '_' + code[4] + '_'
        fig.savefig(self.plot_path + '_' + str(resolution) + '_' + info + '_BDrate')

    def max_len(self, bd):
        # max should be set by work out mode
        maxnum = 9
        for rate in bd:
            if maxnum < max(option.mode[0:len(rate)]):
                maxnum = max(option.mode[0:len(rate)])
        return maxnum+1

    def fix_arr(self, bdrate):
        max = self.max_len(bdrate)
        for rate in bdrate:
            modelist = [0 for i in range(max)]
            for i in range(len(rate)):
                modelist[option.mode[i]] = rate[i]
            if len(rate) < max:
                for i in range(max - len(rate)):
                    rate.append(0)
            for i in range(len(rate)):
                rate[i] = modelist[i]
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
        biao.set_title('%s' % resolution + 'p   ' + 'BD-PSNR')
        chart.set_title('%s' % resolution + 'p')
        chart.set_xlabel('bit_rate')
        chart.set_ylabel('PSNR')
        chart.grid(True)
        for encode in range(len(encode_name)):
            for mode in range(len(encdoe_bitrate[encode])):
                chart.plot(encdoe_bitrate[encode][mode], encode_psnr[encode][mode], '-o',
                           label=encode_name[encode] + '_' + str(mode))
        chart.legend(loc=0)
        rowlabel = self.label_len(encode_bdpsnr, 'bit')
        trans_psnr = self.trans_list(self.fix_arr(encode_bdpsnr))
        biao.table(cellText=trans_psnr, colLabels=encode_name, rowLabels=rowlabel, loc=0,
                   colWidths=[0.3 for i in range(len(encode_name))], edges='horizontal')
        info = ''
        for code in option.codec:
            info += '_' + code[4]
        fig.savefig(self.plot_path + '_' + str(resolution) + info + '_bit_rate')

    def show(self):
        self.bd_data_choose()
        self.bitrate_data_choos()
        self.all_detail()
