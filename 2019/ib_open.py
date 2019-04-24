import time
import datetime
import copy
import pandas as pd
import redis
import os
import pickle
import sys

from myconn import myconn
from collections import deque, namedtuple
from ib_insync import LimitOrder, Future, IB, util, StopLimitOrder


"""
ib自动下单
根据方案24的信号，以ib下单
"""


data = []

def interval_ma60(hengpan=0):
    """
    以60均线分波
    :param st: 开始日期
    :param ed: 终止日期
    :param database: 数据库类型
    :return: 计算结果列表
    """
    short, long, phyd = 12, 26, 9

    cou = []
    zts = [('开始时间', '结束时间', '开盘', '最高', '最低', '收盘', '成交量', '60均线上/下方(1/0)', 'K线数量',
            '涨/跌趋势(+/-)', '此波幅度', 'macd绿区', 'macd红区', '异动小于-1.5倍', '异动大于1.5倍')]
    dc2 = []  # [i[4] for i in data]
    dc = []
    yddy, ydxy = 0, 0  # 异动
    _vol = 0  # 成交量

    i = 0
    _getCou = None
    dates = []

    def get_cou():
        st = cou[-2][0]
        ed = cou[-1][0]
        _O = dc2[st]
        _H = max(dc2[st:ed + 1])
        _L = min(dc2[st:ed + 1])
        _C = dc2[ed]
        jc = _H - _L
        if hengpan and jc < hengpan:
            return None
        zt = '+' if dc2[st:ed + 1].index(_H) > int((ed - st) / 2) else '-'
        # if 1: #jc > 50:
        _dc = dc[st:ed + 1]
        _macdg = len([_m for _m in range(len(_dc)) if
                      (_m == 0 and _dc[_m]['macd'] < 0) or (_dc[_m]['macd'] < 0 and _dc[_m - 1]['macd'] > 0)])
        _macdr = len([_m for _m in range(len(_dc)) if
                      (_m == 0 and _dc[_m]['macd'] > 0) or (_dc[_m]['macd'] > 0 and _dc[_m - 1]['macd'] < 0)])

        return (
            str(dates[st][0]), str(dates[i][0]), _O, _H, _L, _C, _vol, cou[-1][1], ed - st, zt, jc, _macdg, _macdr, ydxy,
            yddy)

    # lend_ = len(data) - 1
    # for i, (d, o, h, l, c, v) in enumerate(data):

    while True:
        d, o, h, l, c, v = yield _getCou
        _getCou = None
        dc2.append(c)
        dates.append((d, o))
        dc.append({'ema_short': 0, 'ema_long': 0, 'diff': 0, 'dea': 0, 'macd': 0,
                   'var': 0,  # 方差
                   'std': 0,  # 标准差
                   'mul': 0,  # 异动
                   })
        if i == 1:
            ac = dc2[i - 1]
            this_c = dc2[i]
            dc[i]['ema_short'] = ac + (this_c - ac) * 2 / short
            dc[i]['ema_long'] = ac + (this_c - ac) * 2 / long
            # dc[i]['ema_short'] = sum([(short-j)*da[i-j][4] for j in range(short)])/(3*short)
            # dc[i]['ema_long'] = sum([(long-j)*da[i-j][4] for j in range(long)])/(3*long)
            dc[i]['diff'] = dc[i]['ema_short'] - dc[i]['ema_long']
            dc[i]['dea'] = dc[i]['diff'] * 2 / phyd
            dc[i]['macd'] = 2 * (dc[i]['diff'] - dc[i]['dea'])
            # co = 1 if dc[i]['macd'] >= 0 else 0
        elif i > 1:
            n_c = dc2[i]
            dc[i]['ema_short'] = dc[i - 1]['ema_short'] * (short - 2) / short + n_c * 2 / short
            dc[i]['ema_long'] = dc[i - 1]['ema_long'] * (long - 2) / long + n_c * 2 / long
            dc[i]['diff'] = dc[i]['ema_short'] - dc[i]['ema_long']
            dc[i]['dea'] = dc[i - 1]['dea'] * (phyd - 2) / phyd + dc[i]['diff'] * 2 / phyd
            dc[i]['macd'] = 2 * (dc[i]['diff'] - dc[i]['dea'])

        if i >= 60:
            _m60 = round(sum(j for j in dc2[i - 59:i + 1]) / 60)

            ma = 60
            std_pj = sum(dc2[i - j] - dates[i - j][1] for j in range(ma)) / ma
            dc[i]['var'] = sum((dc2[i - j] - dates[i - j][1] - std_pj) ** 2 for j in range(ma)) / ma  # 方差 i-ma+1,i+1
            dc[i]['std'] = float(dc[i]['var'] ** 0.5)  # 标准差
            price = c - o
            dc[i]['mul'] = _yd = round(price / dc[i]['std'], 2)
            if _yd > 1.5:
                yddy += 1
            elif _yd < -1.5:
                ydxy += 1
            _vol += v
            if c >= _m60:
                if cou and cou[-1][1] != 0:  # and not is_bs(dc[i-10:i+1],_m60,'<'):
                    cou.append((i, 0))
                    _getCou = get_cou()
                    yddy, ydxy = 0, 0
                    _vol = 0
                    if _getCou:
                        zts.append(_getCou)
                elif not cou:
                    cou.append((i, 0))
                # elif i == lend_:  # data[i][0].day != data[i - 1][0].day or (data[i][0].day == data[i - 1][0].day and str(data[i][0])[11:16] == '09:15') or
                #     cou.append((i, 0))
                #     _getCou = get_cou()
                #     yddy, ydxy = 0, 0
                #     _vol = 0
                #     if _getCou:
                #         zts.append(_getCou)
            else:
                if cou and cou[-1][1] != 1:  # and not is_bs(dc[i-10:i+1],_m60,'>'):
                    cou.append((i, 1))
                    _getCou = get_cou()
                    yddy, ydxy = 0, 0
                    _vol = 0
                    if _getCou:
                        zts.append(_getCou)
                elif not cou:
                    cou.append((i, 1))
                # elif i == lend_:  # data[i][0].day != data[i - 1][0].day or (data[i][0].day == data[i - 1][0].day and str(data[i][0])[11:16] == '09:15') or
                #     cou.append((i, 1))
                #     _getCou = get_cou()
                #     yddy, ydxy = 0, 0
                #     _vol = 0
                #     if _getCou:
                #         zts.append(_getCou)
        i += 1


def to_change():
    # data.pop(0)
    dc = []
    dc2 = [] #[i[5] for i in data]
    short, long, phyd = 12, 26, 9
    # for i,(d,_et,o,h,l,c,*_) in enumerate(data):
    data = []
    res = None
    i = 0
    while True:
        (d, _et, o, h, l, c, *_) = yield res
        dc2.append(c)
        data.append((d, _et, o, h, l, c))
        dc.append({'ema_short': 0, 'ema_long': 0, 'diff': 0, 'dea': 0, 'macd': 0,
                   # 'var': 0,  # 方差
                   # 'std': 0,  # 标准差
                   # 'mul': 0,  # 异动
                   })
        if i == 1:
            ac = data[i - 1][5]
            dc[i]['ema_short'] = ac + (c - ac) * 2 / short
            dc[i]['ema_long'] = ac + (c - ac) * 2 / long
            # dc[i]['ema_short'] = sum([(short-j)*da[i-j][4] for j in range(short)])/(3*short)
            # dc[i]['ema_long'] = sum([(long-j)*da[i-j][4] for j in range(long)])/(3*long)
            dc[i]['diff'] = dc[i]['ema_short'] - dc[i]['ema_long']
            dc[i]['dea'] = dc[i]['diff'] * 2 / phyd
            dc[i]['macd'] = 2 * (dc[i]['diff'] - dc[i]['dea'])
            # co = 1 if dc[i]['macd'] >= 0 else 0
        elif i > 1:
            dc[i]['ema_short'] = dc[i - 1]['ema_short'] * (short - 2) / short + c * 2 / short
            dc[i]['ema_long'] = dc[i - 1]['ema_long'] * (long - 2) / long + c * 2 / long
            dc[i]['diff'] = dc[i]['ema_short'] - dc[i]['ema_long']
            dc[i]['dea'] = dc[i - 1]['dea'] * (phyd - 2) / phyd + dc[i]['diff'] * 2 / phyd
            dc[i]['macd'] = 2 * (dc[i]['diff'] - dc[i]['dea'])

        if i >= 60:
            ma = 60
            std_pj = sum(dc2[i - j] - data[i - j][2] for j in range(ma)) / ma
            # dc[i]['var'] = sum((dc2[i - j] - data[i - j][2] - std_pj) ** 2 for j in range(ma)) / ma  # 方差 i-ma+1,i+1
            # dc[i]['std'] = dc[i]['var'] ** 0.5  # 标准差
            var = sum((dc2[i - j] - data[i - j][2] - std_pj) ** 2 for j in range(ma)) / ma  # 方差 i-ma+1,i+1
            std = var ** 0.5  # 标准差
            price = c - o
            # dc[i]['mul'] = _yd = round(price / dc[i]['std'], 2)
            _yd = round(price / std, 2)
        else:
            _yd = 0
        res = (_et, _yd, o - c)
        i += 1

class ZB(object):
    fa_doc = {
        "24": ["以60均线分波，异动大于3倍，则做多，累积加仓，最大8手；出现反向的波幅大于60平仓，或者出现做空信号平仓。",
               "以60均线分波，异动小于-3倍，则做空，累积加仓，最大8手；出现反向的波幅大于60平仓，或者出现做多信号平仓。", "止损290个点。"],
    }

    def __init__(self):
        # self.da = [(d[0], d[1], d[2], d[3], d[4]) for d in df.values]
        self.xzfa = {'24': self.fa24}  # 执行方案 '8':self.fa8, '5':self.fa5,
        self.database = 'sql'
    @property
    def zdata(self):
        return self._data

    @zdata.setter
    def zdata(self, ds):
        if isinstance(ds, pd.DataFrame):
            self._data = [(d[0], d[1], d[2], d[3], d[4]) for d in ds.values]
        elif isinstance(ds, (tuple, list)):
            self._data = ds
        else:
            raise ValueError("zdata set ds,ds is not list or tuple or DataFrame! ")

    def get_doc(self, fa):
        return self.fa_doc.get(fa)

    def is_date(self, datetimes):
        ''' 是否已经或即将进入晚盘 '''
        h = datetimes.hour
        return (h == 16 and datetimes.minute >= 13) or h > 16 or h < 9

    def time_pd(self, dt1, dt2, fd=1):
        ''' 时间长度 '''
        dt1 = int(str(dt1)[11:16].replace(':', ''))
        dt2 = int(dt2[11:16].replace(':', ''))
        return dt1 - dt2 > fd

    def dt_kc(self, datetimes):
        ''' 开仓时间 '''
        h = datetimes.hour
        return (16 > h >= 9) or (h == 16 and datetimes.minute < 8)

    def sendNone(self, s):
        try:
            s.send(None)
        except:
            pass

    def vis(self, da, ma=60, short=12, long=26, phyd=9, k_min=5):
        ''' 各种指标初始化计算，动态计算 '''
        # da格式：((datetime.datetime(2018, 3, 19, 9, 22),31329.0,31343.0,31328.0,31331.0,249)...)
        dc = deque()
        overlap1 = None  # diff 从下往上交叉
        overlap0 = None  # diff 从上往下交叉
        _O = namedtuple('O', ['lastClose', 'lastDiff'])
        co = 0
        cds = 1
        k_5 = 1  # 5 分钟数据以计算 K指标

        def body_k(o, h, l, c):
            if abs(h - l) > 0:
                return abs(o - c) / abs(h - l) > 0.6
            else:
                return False

        for i in range(len(da)):
            """
            ma60:移动平均值60均线, var:方差, std:标准差, reg:Macd区间, mul:异动重合, k:KDJ的K值, 
            overlap:diff与dea上/下交叉(1/-1),deviation: 底/顶背离(1/-1)
            """
            dc.append(
                {'ema_short': 0, 'ema_long': 0, 'diff': 0, 'dea': 0, 'macd': 0, 'ma60': 0, 'var': 0, 'std': 0, 'reg': 0,
                 'mul': 0, 'datetimes': da[i][0], 'open': da[i][1], 'high': da[i][2], 'low': da[i][3],
                 'close': da[i][4], 'cd': 0, 'maidian': 0, 'open5': da[i][1], 'high5': da[i][2], 'low5': da[i][3],
                 'close5': da[i][4], 'k': 50, 'overlap': 0, 'deviation': 0, 'ma5': 0, 'ma10': 0, 'ma30': 0, 'ma120': 0,
                 'ma72': 0, 'ma200': 0})
            if i == 1:
                ac = da[i - 1][4]
                this_c = da[i][4]
                dc[i]['ema_short'] = ac + (this_c - ac) * 2 / short
                dc[i]['ema_long'] = ac + (this_c - ac) * 2 / long
                # dc[i]['ema_short'] = sum([(short-j)*da[i-j][4] for j in range(short)])/(3*short)
                # dc[i]['ema_long'] = sum([(long-j)*da[i-j][4] for j in range(long)])/(3*long)
                dc[i]['diff'] = dc[i]['ema_short'] - dc[i]['ema_long']
                dc[i]['dea'] = dc[i]['diff'] * 2 / phyd
                dc[i]['macd'] = 2 * (dc[i]['diff'] - dc[i]['dea'])
                co = 1 if dc[i]['macd'] >= 0 else 0
            elif i > 1:
                n_c = da[i][4]
                dc[i]['ema_short'] = dc[i - 1]['ema_short'] * (short - 2) / short + n_c * 2 / short
                dc[i]['ema_long'] = dc[i - 1]['ema_long'] * (long - 2) / long + n_c * 2 / long
                dc[i]['diff'] = dc[i]['ema_short'] - dc[i]['ema_long']
                dc[i]['dea'] = dc[i - 1]['dea'] * (phyd - 2) / phyd + dc[i]['diff'] * 2 / phyd
                dc[i]['macd'] = 2 * (dc[i]['diff'] - dc[i]['dea'])

                # overlap 上一个K线的收盘价，上一个K线的diff
                # deviation 底背离:=REF(C,A1+1)>C AND DIFF>REF(DIFF,A1+1) AND CROSS(DIFF,DEA)
                if dc[i]['diff'] > dc[i]['dea'] and dc[i - 2]['diff'] < dc[i - 2]['dea']:  # 底背离
                    dc[i]['overlap'] = 1
                    _o_ = _O(dc[i - 1]['close'], dc[i - 1]['diff'])
                    if overlap1 and (overlap1.lastClose > dc[i]['close'] and dc[i]['diff'] > overlap1.lastDiff):
                        dc[i]['deviation'] = 1
                    overlap1 = _o_
                elif dc[i]['diff'] < dc[i]['dea'] and dc[i - 2]['diff'] > dc[i - 2]['dea']:  # 顶背离
                    dc[i]['overlap'] = -1
                    _o_ = _O(dc[i - 1]['close'], dc[i - 1]['diff'])
                    if overlap0 and (overlap0.lastClose < dc[i]['close'] and dc[i]['diff'] < overlap0.lastDiff):
                        dc[i]['deviation'] = -1
                    overlap0 = _o_

                # 计算RSI
                # len_dc=len(dc)
                # rsia=0
                # rsib=0
                # for rsi in range(len_dc-14,len_dc):
                #     A=dc[rsi]['close']-dc[rsi]['open']
                #     if A>0:
                #         rsia+=A
                #     else:
                #         rsib+=(-A)
                # dc[i]['rsi'] = rsia/(rsia+rsib)*100

            if k_5 % k_min == 0:
                dc[i]['open5'] = dc[i - k_min + 1]['open5']
                dc[i]['high5'] = max(dc[i - j]['high5'] for j in range(k_min))
                dc[i]['low5'] = min(dc[i - j]['low5'] for j in range(k_min))
            k_5 += 1

            if i >= ma - 1:
                dc[i]['ma60'] = sum(da[i - j][4] for j in range(ma)) / ma  # 移动平均值 60均线
                dc[i]['ma5'] = sum(da[i - j][4] for j in range(5)) / 5  # 移动平均值 5均线
                dc[i]['ma10'] = sum(da[i - j][4] for j in range(10)) / 10  # 移动平均值 10均线
                dc[i]['ma30'] = sum(da[i - j][4] for j in range(30)) / 30  # 移动平均值 30均线
                std_pj = sum(da[i - j][4] - da[i - j][1] for j in range(ma)) / ma
                dc[i]['var'] = sum((da[i - j][4] - da[i - j][1] - std_pj) ** 2 for j in range(ma)) / ma  # 方差 i-ma+1,i+1
                dc[i]['std'] = float(dc[i]['var'] ** 0.5)  # 标准差

                if dc[i]['macd'] >= 0 and dc[i - 1]['macd'] < 0:
                    co += 1
                elif dc[i]['macd'] < 0 and dc[i - 1]['macd'] >= 0:
                    co += 1
                dc[i]['reg'] = co
                price = dc[i]['close'] - dc[i]['open']
                std = dc[i]['std']
                if std:
                    dc[i]['mul'] = round(price / std, 2)

                o1 = dc[i]['open']
                h1 = dc[i]['high']
                l1 = dc[i]['low']
                c1 = dc[i]['close']
                if abs(dc[i]['mul']) > 1.5 and body_k(o1, h1, l1, c1):
                    for j in range(i - 2, i - 15, -1):
                        o2 = dc[j]['open']
                        h2 = dc[j]['high']
                        l2 = dc[j]['low']
                        c2 = dc[j]['close']
                        oc = [o1, o2, c1, c2]
                        oc.sort()
                        try:
                            if not (max([o1, c1]) > min([o2, c2]) and min([o1, c1]) < max([o2, c2])):
                                continue
                            if abs(dc[j]['mul']) > 1.5 and ((o1 > c1 and o2 > c2) or (o1 < c1 and o2 < c2)) and body_k(
                                    o2, h2, l2, c2):
                                if o1 < c1:
                                    if dc[j]['cd'] == 0 and (oc[2] - oc[1]) / (
                                            oc[3] - oc[0]) > 0.4 and o2 < o1 < c2 < c1:
                                        dc[i]['cd'] = cds
                                        cds += 1
                                        break
                                elif o1 > c1:
                                    if dc[j]['cd'] == 0 and (oc[2] - oc[1]) / (
                                            oc[3] - oc[0]) > 0.4 and c1 < c2 < o1 < o2:
                                        dc[i]['cd'] = -cds
                                        cds += 1
                                        break

                            elif abs(dc[j]['mul']) > 1.5 and (
                                    o1 > c1 and o2 < c2 and (h1 <= h2 and l1 <= l2 or c1 <= o2)) and body_k(o2, h2, l2,
                                                                                                            c2):
                                if (oc[2] - oc[1]) / (oc[3] - oc[0]) > 0.4:
                                    dc[i]['maidian'] = -cds
                                    break

                            elif abs(dc[j]['mul']) > 1.5 and (o1 < c1 and o2 > c2) and (
                                    h1 >= h2 and l1 >= l2 or c1 >= o2) and body_k(o2, h2, l2, c2):
                                if (oc[2] - oc[1]) / (oc[3] - oc[0]) > 0.4:
                                    dc[i]['maidian'] = cds
                                    break
                        except:
                            continue

        data = 1  # data future is list
        while data:
            data = yield dc
            len_dc = len(dc)
            if len_dc > 120:
                dc.popleft()
                ind = len_dc-1
            else:
                ind = len_dc
            if isinstance(data, tuple) or isinstance(data, list):
                dc.append({'ema_short': 0, 'ema_long': 0, 'diff': 0, 'dea': 0, 'macd': 0, 'ma60': 0, 'var': 0, 'std': 0,
                           'reg': 0, 'mul': 0, 'datetimes': data[0], 'open': data[1], 'high': data[2], 'low': data[3],
                           'close': data[4], 'cd': 0, 'maidian': 0, 'open5': data[1], 'high5': data[2], 'low5': data[3],
                           'close5': data[4], 'k': 50, 'overlap': 0, 'deviation': 0, 'ma5': 0, 'ma10': 0, 'ma30': 0,
                           'ma120': 0, 'ma72': 0, 'ma200': 0})
                try:
                    dc[ind]['ema_short'] = dc[ind - 1]['ema_short'] * (short - 2) / short + dc[ind][
                        'close'] * 2 / short  # 当日EMA(12)
                    dc[ind]['ema_long'] = dc[ind - 1]['ema_long'] * (long - 2) / long + dc[ind][
                        'close'] * 2 / long  # 当日EMA(26)
                    dc[ind]['diff'] = dc[ind]['ema_short'] - dc[ind]['ema_long']
                    dc[ind]['dea'] = dc[ind - 1]['dea'] * (phyd - 2) / phyd + dc[ind]['diff'] * 2 / phyd
                    dc[ind]['macd'] = 2 * (dc[ind]['diff'] - dc[ind]['dea'])

                    dc[ind]['ma60'] = sum(dc[ind - j]['close'] for j in range(ma)) / ma  # 移动平均值 60均线

                    dc[ind]['ma5'] = sum(dc[ind - j]['close'] for j in range(5)) / 5  # 移动平均值 5均线
                    dc[ind]['ma10'] = sum(dc[ind - j]['close'] for j in range(10)) / 10  # 移动平均值 10均线
                    dc[ind]['ma30'] = sum(dc[ind - j]['close'] for j in range(30)) / 30  # 移动平均值 30均线
                    dc[ind]['ma72'] = sum(dc[ind - j]['close'] for j in range(72)) / 72 if ind >= 71 else 0  # 移动平均值 72均线
                    dc[ind]['ma120'] = (sum(dc[ind - j]['close'] for j in range(120)) / 120) if ind >= 119 else 0  # 移动平均值 120均线
                    dc[ind]['ma200'] = (sum(dc[ind - j]['close'] for j in range(200)) / 200) if ind >= 199 else 0  # 移动平均值 200均线
                    std_pj = sum(dc[ind - j]['close'] - dc[ind - j]['open'] for j in range(ma)) / ma
                    dc[ind]['var'] = sum(
                        (dc[ind - j]['close'] - dc[ind - j]['open'] - std_pj) ** 2 for j in range(ma)) / ma  # 方差
                    dc[ind]['std'] = float(dc[ind]['var'] ** 0.5)  # 标准差

                    # overlap 上一个K线的收盘价，上一个K线的diff
                    # deviation 底背离:=REF(C,A1+1)>C AND DIFF>REF(DIFF,A1+1) AND CROSS(DIFF,DEA)
                    if dc[ind]['diff'] > dc[ind]['dea'] and dc[ind - 2]['diff'] < dc[ind - 2]['dea']:
                        dc[ind]['overlap'] = 1
                        _o_ = _O(dc[ind - 1]['close'], dc[ind - 1]['diff'])
                        if overlap1 and (overlap1.lastClose > dc[ind]['close'] and dc[ind]['diff'] > overlap1.lastDiff):
                            dc[ind]['deviation'] = 1
                        overlap1 = _o_
                    elif dc[ind]['diff'] < dc[ind]['dea'] and dc[ind - 2]['diff'] > dc[ind - 2]['dea']:
                        dc[ind]['overlap'] = -1
                        _o_ = _O(dc[ind - 1]['close'], dc[ind - 1]['diff'])
                        if overlap0 and (overlap0.lastClose < dc[ind]['close'] and dc[ind]['diff'] < overlap0.lastDiff):
                            dc[ind]['deviation'] = -1
                        overlap0 = _o_

                    # 计算K 指标
                    # 计算K 指标
                    # n日RSV =（Cn－Ln） / （Hn－Ln）×100
                    # 公式中，Cn为第n日收盘价；Ln为n日内的最低价；Hn为n日内的最高价。
                    # 其次，计算K值与D值：
                    # 当日K值 = 2 / 3×前一日K值 + 1 / 3×当日RSV
                    # 当日D值 = 2 / 3×前一日D值 + 1 / 3×当日K值
                    # 若无前一日K
                    # 值与D值，则可分别用50来代替。
                    if k_5 % k_min == 0:
                        Ln = min(dc[ind - j]['low'] for j in range(0, k_min * 9, k_min))
                        Hn = max(dc[ind - j]['high'] for j in range(0, k_min * 9, k_min))
                        rsv = (data[4] - Ln) / (Hn - Ln) * 100
                        dc[ind]['k'] = dc[ind - 1]['k'] * 2 / 3 + rsv / 3
                    else:
                        dc[ind]['k'] = dc[ind - 1]['k']
                    k_5 += 1
                    # Cn = da[i][4]
                    # Ln = min(da[i - j][3] for j in range(9))
                    # Hn = max(da[i - j][2] for j in range(9))
                    # rsv = (Cn - Ln) / (Hn - Ln) * 100
                    # dc[i]['k'] = dc[i - 1]['k'] * 2 / 3 + rsv / 3
                    # 计算RSI
                    # len_dc = len(dc)
                    # rsia = 0
                    # rsib = 0
                    # for rsi in range(len_dc - 14, len_dc):
                    #     A = dc[rsi]['close'] - dc[rsi]['open']
                    #     if A > 0:
                    #         rsia += A
                    #     else:
                    #         rsib += (-A)
                    # dc[i]['rsi'] = rsia / (rsia + rsib) * 100
                except Exception as exc:
                    print('DataIndex.py vis', exc)

                if dc[ind]['macd'] >= 0 and dc[ind - 1]['macd'] < 0:
                    co += 1
                elif dc[ind]['macd'] < 0 and dc[ind - 1]['macd'] >= 0:
                    co += 1
                dc[ind]['reg'] = co
                price = dc[ind]['close'] - dc[ind]['open']
                std = dc[ind]['std']
                if std:
                    dc[ind]['mul'] = round(price / std, 2)

                o1 = dc[ind]['open']
                h1 = dc[ind]['high']
                l1 = dc[ind]['low']
                c1 = dc[ind]['close']
                if abs(dc[ind]['mul']) > 1.5 and body_k(o1, h1, l1, c1):
                    for j in range(ind - 1, ind - 12, -1):
                        o2 = dc[j]['open']
                        h2 = dc[j]['high']
                        l2 = dc[j]['low']
                        c2 = dc[j]['close']
                        try:
                            if not (max([o1, c1]) > min([o2, c2]) and min([o1, c1]) < max([o2, c2])):
                                continue
                            oc = [o1, o2, c1, c2]
                            oc.sort()
                            mul_15 = abs(dc[j]['mul'])
                            if mul_15 > 1.5 and ((o1 > c1 and o2 > c2) or (o1 < c1 and o2 < c2)) and body_k(
                                    o2, h2, l2, c2):
                                if o1 < c1:
                                    if dc[j]['cd'] == 0 and (oc[2] - oc[1]) / (oc[3] - oc[0]) > 0.4:
                                        dc[ind]['cd'] = cds
                                        cds += 1
                                        break
                                elif o1 > c1:
                                    if dc[j]['cd'] == 0 and (oc[2] - oc[1]) / (oc[3] - oc[0]) > 0.4:
                                        dc[ind]['cd'] = -cds
                                        cds += 1
                                        break
                            elif mul_15 > 1.5 and (o1 > c1 and o2 < c2 and (
                                    h1 <= h2 and l1 <= l2 or c1 <= o2)):  # and body_k(o2, h2, l2,c2):
                                if (oc[2] - oc[1]) / (oc[3] - oc[0]) > 0.4:
                                    dc[ind]['maidian'] = -cds
                                    break

                            elif mul_15 > 1.5 and (o1 < c1 and o2 > c2) and (
                                    h1 >= h2 and l1 >= l2 or c1 >= o2):  # and body_k(o2, h2, l2,c2):
                                if (oc[2] - oc[1]) / (oc[3] - oc[0]) > 0.4:
                                    dc[ind]['maidian'] = cds
                                    break
                        except Exception as exc:
                            continue
            else:
                print('data不是tuple', type(data), data)

    def dynamic_index(self, data, _ma=60, zsjg=-100):
        ''' 动态交易指标 '''
        res = {}
        is_d = 0
        is_k = 0
        # conn=get_conn('carry_investment')
        # sql='SELECT a.datetime,a.open,a.high,a.low,a.close FROM futures_min a INNER JOIN (SELECT DATETIME FROM futures_min ORDER BY DATETIME DESC LIMIT 0,{})b ON a.datetime=b.datetime'.format(_ma)
        # data=getSqlData(conn,sql)
        data2 = self.vis(da=data, ma=_ma)
        dt2 = data2.send(None)
        data = 1
        while data:
            data = yield res
            dates = data[0]
            res[dates] = {'duo': 0, 'kong': 0, 'mony': 0, 'datetimes': [], 'dy': 0, 'xy': 0}
            # str_time1=None if is_d==0 else str_time1
            # str_time2=None if is_k==0 else str_time2
            jg_d = 0 if is_d == 0 else jg_d
            jg_k = 0 if is_k == 0 else jg_k
            is_dk = not (is_k or is_d)
            # data格式：(datetime.datetime(2018, 3, 26, 20, 19), 30606.0, 30610.0, 30592.0, 30597.0)
            dt2 = data2.send(data)
            if dt2:
                dt2 = dt2[-1]
            datetimes, clo, macd, mas, std, reg, mul = dt2['datetimes'], dt2['close'], dt2['macd'], dt2['ma60'], dt2[
                'std'], dt2['reg'], dt2['mul']
            # if mul>1.5:
            #     res[dates]['dy']+=1
            # if mul<-1.5:
            #     res[dates]['xy']+=1
            if clo < mas and mul < -1.5 and is_dk and self.dt_kc(datetimes):
                jg_d = clo
                str_time1 = str(datetimes)
                res[dates]['datetimes'].append([str_time1, 1])
                is_d = 1
            elif clo > mas and mul > 1.5 and is_dk and self.dt_kc(datetimes):
                jg_k = clo
                str_time2 = str(datetimes)
                res[dates]['datetimes'].append([str_time2, -1])
                is_k = -1
            if is_d == 1 and ((macd < 0 and clo > mas) or clo - jg_d < zsjg or self.is_date(datetimes)):
                if self.time_pd(str(datetimes), str_time1, 3):
                    res[dates]['duo'] += 1
                    res[dates]['mony'] += (clo - jg_d)
                    res[dates]['datetimes'].append([str(datetimes), 2])
                    is_d = 0
            elif is_k == -1 and ((macd > 0 and clo < mas) or jg_k - clo < zsjg or self.is_date(datetimes)):
                if self.time_pd(str(datetimes), str_time2, 3):
                    res[dates]['kong'] += 1
                    res[dates]['mony'] += (jg_k - clo)
                    res[dates]['datetimes'].append([str(datetimes), -2])
                    is_k = 0
        self.sendNone(data2)



    def fa24(self, data, _ma=60, zsjg=-290, ydzs=190, zyds=1000, cqdc=6, reverse=False):
        zsjg2 = zsjg
        _zsjg_d, _zsjg_k = 0, 0
        jg_d, jg_k = 0, 0

        if not os.path.isfile('startMony_d.pkl'):
            startMony_d = []
        else:
            with open('startMony_d.pkl','rb') as f:
                startMony_d = pickle.loads(f.read())
        if not os.path.isfile('startMony_k.pkl'):
            startMony_k = []
        else:
            with open('startMony_k.pkl','rb') as f:
                startMony_k = pickle.loads(f.read())

        str_time1, str_time2 = '', ''
        is_d, is_k = 0, 0
        res = {}
        first_time = []
        last_date = ''
        ydzs_d, ydzs_k = 0, 0  # 移动止损
        zts2 = None
        last_pop = 0

        data2 = self.vis(da=data, ma=_ma)
        dt2 = data2.send(None)
        _zts2 = interval_ma60()
        _zts2.send(None)
        _zts = to_change()
        _zts.send(None)
        zts = []

        data = 1
        kcs = []
        while data:
            # while循环判断，数据重用，一行原始数据，日期，是否强制平仓
            # _while, dt3, dates, qzpc = yield res, first_time
            data = yield kcs
            dates = str(data[0])[:10]
            if dates not in res:
                res[dates] = {'duo': 0, 'kong': 0, 'mony': 0, 'datetimes': [], 'dy': 0, 'xy': 0, 'ch': 0, }

            is_write = False  # 是否把持仓写入pkl文件

            is_dk = not (is_k == -1 or is_d == 1)
            dt2 = data2.send(data[:6])
            if dt2:
                dt2 = dt2[-1]
            (
                datetimes, clo, macd, mas, reg, std,
                mul, cd, high, low
            ) = (
                dt2['datetimes'], dt2['close'], dt2['macd'], dt2['ma60'], dt2['reg'], dt2['std'],
                dt2['mul'], dt2['cd'], dt2['high'], dt2['low']
            )
            datetimes_hour = datetimes.hour

            # if zts2 is None:
            zts2 = _zts2.send(data[:6])
            if zts2 is not None:
                ztss = _zts.send(zts2)
                if ztss:
                    zts.append(ztss)
            str_dt = str(datetimes)
            while len(zts)>1 and zts[0][0] < str_dt:
                if zts[0][0] < str_dt and zts[1][0] >= str_dt:
                    break
                zts.pop(0)
                last_pop = 1
            if mul > 1.5:
                res[dates]['dy'] += 1
            elif mul < -1.5:
                res[dates]['xy'] += 1
            res[dates]['ch'] += 1 if cd != 0 else 0

            kcs = []

            # 开平仓条件
            _zt = zts[0] if zts else ('', 0, 0)
            len_startMony_d = len(startMony_d)
            len_startMony_k = len(startMony_k)

            # 测试
            # kctj_d = _zt[1] > 1 and _zt[2] < 0 and last_pop == 1 and len_startMony_d<8 and (16 > datetimes_hour >= 9) and data[6] == 'SS'
            # kctj_k = _zt[1] < -1 and _zt[2] > 0 and last_pop == 1 and len_startMony_k<8 and (16 > datetimes_hour >= 9) and data[6] == 'SS'
            # 上面两行为了测试，正确应为下面两行
            kctj_d = _zt[1] > 3 and _zt[2] < 0 and last_pop == 1 and len_startMony_d < 8 and (16 > datetimes_hour > 9) and data[6] == 'SS'
            kctj_k = _zt[1] < -3 and _zt[2] > 0 and last_pop == 1 and len_startMony_k < 8 and (16 > datetimes_hour > 9) and data[6] == 'SS'
 
            last_pop = 0
            pctj_d = _zt[2]>60
            pctj_k = _zt[2]<-60


            if reverse:
                kctj_d, kctj_k = kctj_k, kctj_d
                pctj_d, pctj_k = pctj_k, pctj_d

            if kctj_d:
                jg_d = clo
                if len_startMony_d==1:
                    startMony_d.append((str(datetimes),clo))
                    startMony_d.append((str(datetimes), clo))
                    kcs = [str(datetimes), clo, 2]
                elif len_startMony_d==3:
                    startMony_d.append((str(datetimes),clo))
                    startMony_d.append((str(datetimes), clo))
                    startMony_d.append((str(datetimes), clo))
                    kcs = [str(datetimes), clo, 3]
                else:
                    startMony_d.append((str(datetimes), clo))
                    kcs = [str(datetimes), clo, 1]
                str_time1 = str(datetimes)
                is_d = 1
                is_write = True
                first_time = [str_time1, '多', clo]
                zsjg = low - clo - 1 if zsjg2 >= -10 else zsjg
                _zsjg_d = 0

                if startMony_k:
                    for i in startMony_k:
                        res[dates]['kong'] += 1
                        price = round(i[1] - clo, 2)
                        price -= cqdc
                        res[dates]['mony'] += price
                        res[dates]['datetimes'].append([i[0], str(datetimes), '空', price, 0])
                    is_k = 0
                    first_time = []
                    tj_k = 0
                    _zsjg_k = 0
                    ydzs_k = 0
                    startMony_k = []
            elif kctj_k:
                jg_k = clo
                if len_startMony_k==1:
                    startMony_k.append((str(datetimes), clo))
                    startMony_k.append((str(datetimes), clo))
                    kcs = [str(datetimes), clo, -2]
                elif len_startMony_k==3:
                    startMony_k.append((str(datetimes), clo))
                    startMony_k.append((str(datetimes), clo))
                    startMony_k.append((str(datetimes), clo))
                    kcs = [str(datetimes), clo, -3]
                else:
                    startMony_k.append((str(datetimes), clo))
                    kcs = [str(datetimes), clo, -1]
                str_time2 = str(datetimes)
                is_k = -1
                is_write = True
                first_time = [str_time2, '空', clo]
                zsjg = clo - high - 1 if zsjg2 >= -10 else zsjg
                _zsjg_k = 0

                if startMony_d:
                    for i in startMony_d:
                        res[dates]['duo'] += 1
                        price = round(clo - i[1], 2)
                        price -= cqdc
                        res[dates]['mony'] += price
                        res[dates]['datetimes'].append([i[0], str(datetimes), '多', price, 0])
                    is_d = 0
                    first_time = []
                    tj_d = 0
                    _zsjg_d = 0
                    ydzs_d = 0
                    startMony_d = []

            if is_d == 1 and startMony_d:
                ydzs_d = high if (ydzs_d == 0 or high > ydzs_d) else ydzs_d
                _startMony_d = max(startMony_d,key=lambda xm:xm[1])[1]
                high_zs = ydzs_d - _startMony_d
                if high_zs >= ydzs:
                    _zsjg_d = _startMony_d + high_zs * 0.2  # 止损所在价格点，至少盈利20%
                elif _zsjg_d == 0:
                    _zsjg_d = _startMony_d + zsjg  # 止损所在价格点
                if (pctj_d or low <= _zsjg_d) and str(
                    datetimes) != str_time1:
                    if low > _zsjg_d and high - _startMony_d < zyds:
                        zszy = 0  # 正常平仓
                        for i in startMony_d:
                            res[dates]['duo'] += 1
                            price = round(clo - i[1], 2)
                            price -= cqdc
                            res[dates]['mony'] += price
                            res[dates]['datetimes'].append([i[0], str(datetimes), '多', price, zszy])
                        kcs = [str(datetimes), clo, -len(startMony_d)]
                        is_d = 0
                        first_time = []
                        tj_d = 0
                        _zsjg_d = 0
                        ydzs_d = 0
                        startMony_d = []
                        is_write = True
                    elif low <= _zsjg_d:
                        zszy = -1  # 止损
                        for i in startMony_d:
                            res[dates]['duo'] += 1
                            if low <= _zsjg_d <= high:
                                price = round(_zsjg_d - i[1], 2)
                            else:
                                price = round(clo - i[1], 2)
                            price -= cqdc
                            res[dates]['mony'] += price
                            res[dates]['datetimes'].append([i[0], str(datetimes), '多', price, zszy])
                        kcs = [str(datetimes), clo, -len(startMony_d)]
                        is_d = 0
                        first_time = []
                        tj_d = 0
                        _zsjg_d = 0
                        ydzs_d = 0
                        startMony_d = []
                        is_write = True
            elif is_k == -1 and startMony_k:
                ydzs_k = low if (ydzs_k == 0 or ydzs_k > low) else ydzs_k
                _startMony_k = min(startMony_k,key=lambda xm:xm[1])[1]
                low_zs = _startMony_k - ydzs_k
                if low_zs >= ydzs:
                    _zsjg_k = _startMony_k - low_zs * 0.2  # 止损所在价格点，至少盈利20%
                elif _zsjg_k == 0:
                    _zsjg_k = _startMony_k - zsjg  # 止损所在价格点
                if (pctj_k or high >= _zsjg_k) and str(
                    datetimes) != str_time2:
                    if high < _zsjg_k and _startMony_k - low < zyds:
                        zszy = 0  # 正常平仓
                        for i in startMony_k:
                            res[dates]['kong'] += 1
                            price = round(i[1]-clo, 2)
                            price -= cqdc
                            res[dates]['mony'] += price
                            res[dates]['datetimes'].append([i[0], str(datetimes), '空', price, zszy])
                        kcs = [str(datetimes), clo, len(startMony_k)]
                        is_k = 0
                        first_time = []
                        tj_k = 0
                        _zsjg_k = 0
                        ydzs_k = 0
                        startMony_k = []
                        is_write = True
                    elif high >= _zsjg_k:
                        zszy = -1  # 止损
                        for i in startMony_k:
                            res[dates]['kong'] += 1
                            if low <= _zsjg_k <= high:
                                price = round(i[1]-_zsjg_k, 2)
                            else:
                                price = round(i[1] - clo, 2)
                            price -= cqdc
                            res[dates]['mony'] += price
                            res[dates]['datetimes'].append([i[0], str(datetimes), '空', price, zszy])
                        kcs = [str(datetimes), clo, len(startMony_k)]
                        is_k = 0
                        first_time = []
                        tj_k = 0
                        _zsjg_k = 0
                        ydzs_k = 0
                        startMony_k = []
                        is_write = True

            if is_write:
                with open('startMony_k.pkl','wb') as fk, open('startMony_d.pkl','wb') as fd:
                    fk.write(pickle.dumps(startMony_k))
                    fd.write(pickle.dumps(startMony_d))


class Zbjs(ZB):
    __slots__ = ('tab_name', 'zdata', 'xzfa')

    def __init__(self):
        self.tab_name = {'1': 'wh_same_month_min', '2': 'wh_min', '3': 'handle_min', '4': 'index_min'}  # index_min
        super(Zbjs, self).__init__()

    def main(self, data, _ma=60):
        sql = f"SELECT DATETIME,OPEN,high,low,CLOSE,vol FROM wh_same_month_min WHERE prodcode='HSI' ORDER BY DATETIME DESC LIMIT {_ma}"
        
        # data = myconn.getSqlData(conn, sql)
        dyn = self.fa24(data)
        dyn.send(None)
        req = None
        param = 1
        while param:
            param = yield req
            req = dyn.send(param)
        dyn.close()
        self.sendNone(dyn)


def main2():
    _ma = 60
    red = redis.Redis()

    stdate = str(datetime.datetime.now()-datetime.timedelta(3))[:10]
    sql = f"SELECT DATETIME,OPEN,high,low,CLOSE,vol FROM wh_same_month_min WHERE prodcode='HSI' ORDER BY DATETIME DESC LIMIT 100,1600"

    conn = myconn.get_conn('carry_investment')
    # data = myconn.getSqlData(conn, sql)

    dtsql = f"SELECT DATETIME,OPEN,high,low,CLOSE,vol FROM wh_same_month_min WHERE prodcode='HSI' ORDER BY DATETIME DESC LIMIT 100"
    global data
    data = myconn.getSqlData(conn, sql)
    data = list(data)
    data.reverse()
    data_dt = {i[0] for i in data}

    zbjs = Zbjs().main(copy.deepcopy(data))
    zs = zbjs.send(None)
    while True:
        # data2 = list(myconn.getSqlData(conn, dtsql))
        # data2.reverse()
        data2 = pickle.loads(red.get('whfuture_min1'))
        for dt in data2[-200:]:
            dt = list(dt[1:7])
            dt[0] = datetime.datetime.strptime(dt[0],'%Y-%m-%d %H:%M:%S')
            if dt[0] not in data_dt:
                data_dt.add(dt[0])
                data.append(dt)
                zs = zbjs.send(dt)
                # print(dt)
                print(zs, dt[0], 'zs......')
                # print(data[-2:])
                time.sleep(0.1)
        time.sleep(30)



def xiadan(price, vb):
    if vb>0:
        order = LimitOrder('BUY', abs(vb), price, orderRef='PY_WH_3')
    else:
        order = LimitOrder('SELL', abs(vb), price, orderRef='PY_WH_3')
    ib.placeOrder(hsi, order)




def main(ccl=0):
    sql = f"SELECT DATETIME,OPEN,high,low,CLOSE,vol,'LS' FROM wh_same_month_min WHERE prodcode='HSI' ORDER BY DATETIME DESC LIMIT 2300,2600"
    dtsql = f"SELECT DATETIME,OPEN,high,low,CLOSE,vol,'LS' FROM wh_same_month_min WHERE prodcode='HSI' ORDER BY DATETIME DESC LIMIT 0,2300"
    conn = myconn.get_conn('carry_investment')
    data = myconn.getSqlData(conn, sql)
    data = list(data)
    data.reverse()
    data_dt = {i[0] for i in data}
    data2 = myconn.getSqlData(conn, dtsql)
    data2 = list(data2)
    data2.reverse()
    zbjs = Zbjs().main(copy.deepcopy(data))
    zbjs.send(None)
    for dt in data2:
        if dt[0] not in data_dt:
            data_dt.add(dt[0])
            zs = zbjs.send(dt)
            if zs:
                print(zs, dt[0])
    red = redis.Redis()
    logs = open('logger.txt', 'w')
    while True:
        # data2 = list(myconn.getSqlData(conn, dtsql))
        # data2.reverse()
        data2 = pickle.loads(red.get('whfuture_min1'))
        for dt in data2[-10:]:
            dt = list(dt[1:7])
            dt[0] = datetime.datetime.strptime(dt[0],'%Y-%m-%d %H:%M:%S')
            dt.append('SS')  # 用SS标记为实时数据
            if dt[0] not in data_dt:
                data_dt.add(dt[0])
                data.append(dt)
                zs = zbjs.send(dt)
                if zs:
                    if (ccl > 0 and zs[2] < 0) or (ccl < 0 and zs[2] > 0):
                        xiadan(zs[1], -ccl)
                        print(zs[:2]+[-ccl], '下单时间:', str(datetime.datetime.now()))
                        logs.write(str(zs[:2]+[ccl])+'\n')
                        ccl = 0
                    else:
                        ccl += zs[2]
                        xiadan(zs[1], zs[2])
                        print(zs, '下单时间:', str(datetime.datetime.now()))
                        logs.write(str(zs)+'\n')
                    logs.flush()
                    print(f'持仓：{ccl}')
                # print(data[-2:])
                # time.sleep(0.05)
        time.sleep(30)
        

ib = IB()
CODE = 'HSIH9'
ib.connect('192.168.2.204', 7496, clientId=8, timeout=3)
hsi = Future(localSymbol=CODE)
ib.qualifyContracts(hsi)


if __name__ == '__main__':
    argv = sys.argv
    ccl = 0  # 持仓量
    if len(argv) > 1:
        try:
            ccl = int(argv[1])
        except:
            pass
    main(ccl)

