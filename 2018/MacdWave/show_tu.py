import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import TICKLEFT, TICKRIGHT, Line2D
from matplotlib.patches import Rectangle

fig = plt.figure(figsize=(30, 12))
ax = fig.add_subplot(111)
ax1 = ax.twinx()


def DrawDF(df1, filename, b_index, s_index, title):
    """ 绘制K线图 """

    ax.clear()
    ax1.clear()
    k_width = 50
    k_diff = 10
    kline = k_width + k_diff

    for i in df1.iterrows():
        x = i[0] * kline
        O = i[1]['open']
        C = i[1]['close']
        L = i[1]['low']
        H = i[1]['high']
        MACD = i[1]['macd']
        DATE = i[1]['datetime']
        hh = abs(C - O)
        x1 = x + k_width / 2
        if C > O:
            a = False
            y = O
            cc = 'R'
            if i[1]['std1'] >= 1.5:
                a = True
                cc = 'Y'
                if i[1]['std1'] >= 2: cc = 'R'
            # 上影线 下影线
            line1 = Line2D((x1, x1), (C, H), color=cc)
            line2 = Line2D((x1, x1), (O, L), color=cc)

            ax.add_line(line1)
            ax.add_line(line2)
        else:
            a = True
            y = C
            cc = 'C'
            if i[1]['std1'] <= -1.5:
                cc = 'B'
                if i[1]['std1'] <= -2: cc = 'G'
            # 影线
            line = Line2D((x1, x1), (L, H), color=cc)
            ax.add_line(line)
        hh = abs(C - O)
        if i[0] == b_index:
            #             cc='M'
            xx1 = x1
            yy1 = C
        elif i[0] == s_index:
            xx2 = x1
            yy2 = C
        # K线实体
        rec = Rectangle((x, y), k_width, hh, fill=a, color=cc)

        if MACD > 0:
            cc = 'R'
        else:
            cc = 'G'
        # MACD
        line = Line2D((x1, x1), (0, MACD), color=cc, linewidth=k_width / 20, alpha=0.1)
        ax1.add_line(line)
        ax.add_patch(rec)

    # 买卖点连线
    line = Line2D((xx1, xx2), (yy1, yy2), color='B', linestyle='dashed', linewidth=2)
    ax.plot(xx1, yy1, 'm^', xx2, yy2, 'mv', linewidth=30)
    ax.add_line(line)
    xx = list(df1.datetime.apply(str))
    # xx1=list(df1.datetime)
    ax.set_xticklabels([])
    # print(xx)
    # ax1.set_xticklabels(xx[:10])
    ind = np.arange(len(xx))
    ax1.xaxis_date()
    xx_separated = [xx[i] for i in range(0,len(xx),int(len(xx)/8))]
    ax1.set_xticklabels(xx_separated)
    # ax1.plot(xx, ind)

    ax1.set_ylim(-200, 200)

    ax.grid()
    # 均线，MACD黄白线
    ax.plot(df1.index * kline + k_width / 2, df1.ma60, color='r', alpha=1)
    ax.plot(df1.index * kline + k_width / 2, df1.ma30, color='g', alpha=1)
    ax1.plot(df1.index * kline + k_width / 2, df1['diff'], color='w', alpha=1)
    ax1.plot(df1.index * kline + k_width / 2, df1['dea'], color='y', alpha=1)
    # ax1.set_xticklabels([])
    ax.autoscale_view()
    ax.legend()
    ax1.autoscale_view()
    plt.title(str(title), fontsize=20, color='r')
    plt.xticks(rotation=90)
    # fig.xticks(rotation=90)
    fig.savefig(filename)
    return plt


if __name__ == '__main__':
    data = pd.read_pickle(r'D:\tools\Tools\December_2018\2018-12-14\highLowOpen.pick')
    data_macd = pd.read_pickle(r'D:\tools\Tools\December_2018\2018-12-20\data_macd_min.pick')
    for i in data.values:
        st = data_macd[data_macd.datetime == i[0] + ' 09:15:00'].index[0]
        st2 = st - 80
        et = data_macd[data_macd.datetime == i[1]].index[0]
        et2 = st + 780
        plt = DrawDF(data_macd[st2:et2], f'{i[0]}.jpg', st, et, i[0])
        plt.show()
        break
        # print(st,et)
