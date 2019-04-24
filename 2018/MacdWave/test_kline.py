import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import TICKLEFT, TICKRIGHT, Line2D
from matplotlib.patches import Rectangle

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = os.path.join(BASE_DIR, 'AndBefore_2018_3')
sys.path.append(BASE_DIR)
from MyUtil import MongoDBData, sql_data


def get_macd(data):
    short, long, phyd = 12, 26, 9
    dc = []
    data2 = []
    for i, (d, o, h, l, c, v) in enumerate(data):
        dc.append({'ema_short': 0, 'ema_long': 0, 'diff': 0, 'dea': 0, 'macd': 0})
        if i == 1:
            ac = data[i - 1][4]
            dc[i]['ema_short'] = ac + (c - ac) * 2 / short
            dc[i]['ema_long'] = ac + (c - ac) * 2 / long
            # dc[i]['ema_short'] = sum([(short-j)*da[i-j][4] for j in range(short)])/(3*short)
            # dc[i]['ema_long'] = sum([(long-j)*da[i-j][4] for j in range(long)])/(3*long)
            dc[i]['diff'] = dc[i]['ema_short'] - dc[i]['ema_long']
            dc[i]['dea'] = dc[i]['diff'] * 2 / phyd
            dc[i]['macd'] = 2 * (dc[i]['diff'] - dc[i]['dea'])
        elif i > 1:
            dc[i]['ema_short'] = dc[i - 1]['ema_short'] * (short - 2) / short + c * 2 / short
            dc[i]['ema_long'] = dc[i - 1]['ema_long'] * (long - 2) / long + c * 2 / long
            dc[i]['diff'] = dc[i]['ema_short'] - dc[i]['ema_long']
            dc[i]['dea'] = dc[i - 1]['dea'] * (phyd - 2) / phyd + dc[i]['diff'] * 2 / phyd
            dc[i]['macd'] = 2 * (dc[i]['diff'] - dc[i]['dea'])
        if i >= 60:
            ma = 60
            ma30 = sum(data[i - j][4] for j in range(30)) / 30
            ma60 = sum(data[i - j][4] for j in range(60)) / 60
            std_pj = sum(data[i - j][4] - data[i - j][1] for j in range(ma)) / ma
            var = sum((data[i - j][4] - data[i - j][1] - std_pj) ** 2 for j in range(ma)) / ma  # 方差 i-ma+1,i+1
            std = float(var ** 0.5)  # 标准差
            _yd = round((c - o) / std, 2)  # 异动
        else:
            _yd = 0
            ma30 = sum(data[i - j][4] for j in range(i + 1)) / (i + 1) if i < 30 else sum(
                data[i - j][4] for j in range(30)) / 30
            ma60 = sum(data[i - j][4] for j in range(i + 1)) / (i + 1)
        d = str(d)
        data2.append(
            [d, o, h, l, c, _yd, ma30, ma60, round(dc[i]['macd'], 2), round(dc[i]['diff'], 2), round(dc[i]['dea'], 2)])
    return data2


def DrawDF(df1, filename, b_index, s_index, title):
    """ 绘制K线图 """
    fig = plt.figure(figsize=(30, 12))
    ax = fig.add_subplot(111)
    ax1 = ax.twinx()

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
        line = Line2D((x1, x1), (0, MACD), color=cc, linewidth=k_width / 2, alpha=0.1)
        ax1.add_line(line)
        ax.add_patch(rec)

    # 买卖点连线
    line = Line2D((xx1, xx2), (yy1, yy2), color='B', linestyle='dashed', linewidth=2)
    ax.plot(xx1, yy1, 'm^', xx2, yy2, 'mv', linewidth=30)
    ax.add_line(line)
    xx = list(df1.datetime.apply(str))
    # xx1=list(df1.datetime)
    ax.set_xticklabels([])
    ax1.set_xticklabels(xx)

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


#     ax.clear()
#     ax1.clear()
#     fig.clear()
#     plt.close()

if __name__ == '__main__':
    data = sql_data(st='2018-11-08 09:00:00', ed='2018-11-08 23:59:00')
    data = [i for i in data]
    # data: [(datetime.datetime(2018, 11, 8, 9, 15), 26614.0, 26614.0, 26498.0, 26499.0, 2447.0), (datetime.datetime(2018, 11, 8, 9, 16), 26496.0, 26518.0, 26477.0, 26499.0, 1325.0)...]
    d = get_macd(data)
    d = pd.DataFrame(d, columns=['datetime', 'open', 'high', 'low', 'close', 'std1', 'ma30', 'ma60', 'macd', 'diff',
                                 'dea'])
    plt = DrawDF(d, 'a.jpg', 80, 128, '1min')
    plt.show()
