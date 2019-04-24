import os
import sys
import pymongo
import datetime
import math
import time
import pymysql
import pandas as pd
from collections import deque,defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = os.path.join(BASE_DIR, 'AndBefore_2018_3')
sys.path.append(BASE_DIR)
from MyUtil import MongoDBData,sql_data



def highLowOpen(types='sql',st='2018-08-01',et='2018-08-12'):
    """ 高低开 """
    short, long, phyd = 12, 26, 9
    if types == 'sql':
        data = sql_data(st,et)
        n = next(data)
    else:
        data = MongoDBData('HKFuture', 'future_1min').get_hsi(st, et)
        n = next(data)
    clo_l = [n[4]]
    ope_l = [n[1]]
    g, d = [], []
    sg, sd = 0, 0
    dc = [{}]  # deque()
    res = [['日期','结束时间', '高低开多少点', 'macd波数', 'macd波数概率','正向异动', '反向异动','回调60均线空间']]
    macds, ydd, ydx = 0, 0, 0  # macd个数，阳异动个数，阴异动个数
    wpy = defaultdict(int)
    jr = False
    ma60d = 0
    ma60l = []
    macdl = []
    for i, (t, o, h, l, c, v) in enumerate(data, 1):
        clo_l.append(c)
        ope_l.append(o)
        dc.append({'ema_short': 0, 'ema_long': 0, 'diff': 0, 'dea': 0, 'macd': 0,
                   'var': 0,  # 方差
                   'std': 0,  # 标准差
                   'mul': 0,  # 异动
                   })
        if i == 1:
            dc[i]['ema_short'] = clo_l[-2] + (c - clo_l[-2]) * 2 / short
            dc[i]['ema_long'] = clo_l[-2] + (c - clo_l[-2]) * 2 / long
            # dc[i]['ema_short'] = sum([(short-j)*da[i-j][4] for j in range(short)])/(3*short)
            # dc[i]['ema_long'] = sum([(long-j)*da[i-j][4] for j in range(long)])/(3*long)
            dc[i]['diff'] = dc[i]['ema_short'] - dc[i]['ema_long']
            dc[i]['dea'] = dc[i]['diff'] * 2 / phyd
            dc[i]['macd'] = 2 * (dc[i]['diff'] - dc[i]['dea'])

            # co = 1 if dc[i]['macd'] >= 0 else 0
        else:
            dc[i]['ema_short'] = dc[i - 1]['ema_short'] * (short - 2) / short + c * 2 / short
            dc[i]['ema_long'] = dc[i - 1]['ema_long'] * (long - 2) / long + c * 2 / long
            dc[i]['diff'] = dc[i]['ema_short'] - dc[i]['ema_long']
            dc[i]['dea'] = dc[i - 1]['dea'] * (phyd - 2) / phyd + dc[i]['diff'] * 2 / phyd
            dc[i]['macd'] = _macd = 2 * (dc[i]['diff'] - dc[i]['dea'])

            macdl.append(1) if _macd>0 else macdl.append(0)

        if i >= 60:
            ma = 60
            std_pj = sum(clo_l[i - j] - ope_l[i - j] for j in range(ma)) / ma
            dc[i]['var'] = sum((clo_l[i - j] - ope_l[i - j] - std_pj) ** 2 for j in range(ma)) / ma  # 方差 i-ma+1,i+1
            dc[i]['std'] = dc[i]['var'] ** 0.5  # 标准差
            dc[i]['mul'] = _yd = round((c - o) / dc[i]['std'], 2)

            _m60 = round(sum(j for j in clo_l[i - 59:i + 1]) / 60)

            if c>_m60:
                ma60l.append(1)
            elif c<=_m60:
                ma60l.append(0)

        is915 = (t.hour == 9 and t.minute == 15)

        if is915:
            jr = True
            gdk = o - clo_l[-2]
            if gdk > 0:
                g.append(gdk)
                sg += gdk
            elif gdk < 0:
                d.append(-gdk)
                sd += -gdk

        if jr:
            # _m60 = round(sum(j for j in clo_l[i - 59:i + 1]) / 60)
            if macdl[-1] != macdl[-2]:  #(dc[i]['macd'] > 0 and dc[i - 1]['macd'] <= 0) or (dc[i]['macd'] <= 0 and dc[i - 1]['macd'] > 0):
                macds += 1
                ma60d = c

            if _yd > 1.5:
                ydd += 1
            elif _yd < -1.5:
                ydx += 1

            if not is915 and ma60l[-1]!=ma60l[-2]: #((clo_l[-2] > _m60 and c <= _m60) or (clo_l[-2] <= _m60 and c > _m60)):  # (o < c and o <= _m60 and c >= _m60) or (o > c and o >= _m60 and c <= _m60) or
                jr = False
                t2 = str(t)
                wpy[macds] += 1
                res.append([t2[:10],t2, gdk, macds, wpy[macds], ydd, ydx, abs(ma60d-c)])
                macds, ydd, ydx = 0, 0, 0

    return res


def abnormal(types='sql',st='2018-08-01',et='2018-08-12'):
    """
    macd 分波统计
    :param types: 数据库类型，sql、mongodb
    :param st: 开始日期
    :param et: 结束日期
    :param md: macd最小数值
    :return:
    """
    short, long, phyd = 12, 26, 9
    if types == 'sql':
        data = sql_data(st,et)
        n = next(data)
    else:
        data = MongoDBData('HKFuture', 'future_1min').get_hsi(st, et)
        n = next(data)
    clo_l = [n[4]]
    ope_l = [n[1]]

    dc = [{}]  # deque()
    res = [['开始时间', '结束时间', '开盘价', '最高价', '最低价', '收盘价', 'K线数量', '60均线上方K线数量',
            'macd红区在60均线波号', 'macd绿区在60均线波号', '异动大于1.5倍', '异动小于-1.5倍', '异动大于2倍', '异动小于-2倍']]
    ydd, ydx, ydd2, ydx2 = 0, 0, 0, 0  # 阳异动1.5倍个数，阴异动1.5倍个数，阳异动2倍个数，阴异动2倍个数
    macdr,macdg = 0, 0
    macdks, macdks60 = 0,0  # 此波macdK线数量、60均线以上的数量
    for i, (t, o, h, l, c, v) in enumerate(data, 1):
        clo_l.append(c)
        ope_l.append(o)
        dc.append({'ema_short': 0, 'ema_long': 0, 'diff': 0, 'dea': 0, 'macd': 0,
                   'var': 0,  # 方差
                   'std': 0,  # 标准差
                   'mul': 0,  # 异动
                   })
        if i == 1:
            dc[i]['ema_short'] = clo_l[-2] + (c - clo_l[-2]) * 2 / short
            dc[i]['ema_long'] = clo_l[-2] + (c - clo_l[-2]) * 2 / long
            # dc[i]['ema_short'] = sum([(short-j)*da[i-j][4] for j in range(short)])/(3*short)
            # dc[i]['ema_long'] = sum([(long-j)*da[i-j][4] for j in range(long)])/(3*long)
            dc[i]['diff'] = dc[i]['ema_short'] - dc[i]['ema_long']
            dc[i]['dea'] = dc[i]['diff'] * 2 / phyd
            dc[i]['macd'] = 2 * (dc[i]['diff'] - dc[i]['dea'])

            # co = 1 if dc[i]['macd'] >= 0 else 0
        else:
            dc[i]['ema_short'] = dc[i - 1]['ema_short'] * (short - 2) / short + c * 2 / short
            dc[i]['ema_long'] = dc[i - 1]['ema_long'] * (long - 2) / long + c * 2 / long
            dc[i]['diff'] = dc[i]['ema_short'] - dc[i]['ema_long']
            dc[i]['dea'] = dc[i - 1]['dea'] * (phyd - 2) / phyd + dc[i]['diff'] * 2 / phyd
            dc[i]['macd'] = 2 * (dc[i]['diff'] - dc[i]['dea'])

        if i >= 60:
            ma = 60
            if i == 60:
                _o, _h, _l = n[1], n[2], n[3]
                _sdate = n[0]
            std_pj = sum(clo_l[i - j] - ope_l[i - j] for j in range(ma)) / ma
            dc[i]['var'] = sum((clo_l[i - j] - ope_l[i - j] - std_pj) ** 2 for j in range(ma)) / ma  # 方差 i-ma+1,i+1
            dc[i]['std'] = dc[i]['var'] ** 0.5  # 标准差
            dc[i]['mul'] = _yd = round((c - o) / dc[i]['std'], 2)


            _m60 = round(sum(j for j in clo_l[i - 59:i + 1]) / 60)
            if (dc[i]['macd'] > 0 and dc[i - 1]['macd'] <= 0) or (dc[i]['macd'] <= 0 and dc[i - 1]['macd'] > 0):

                macdr += 1 if dc[i]['macd'] <= 0 else 0
                macdg -= 1 if dc[i]['macd'] > 0 else 0

                res.append([_sdate,n[0],_o,_h,_l,n[4],macdks,macdks60,macdr,macdg,ydd,ydx,ydd2,ydx2])

                ydd, ydx, ydd2, ydx2 = 0, 0, 0, 0  # 阳异动1.5倍个数，阴异动1.5倍个数，阳异动2倍个数，阴异动2倍个数
                _sdate, _o, _h, _l = str(t), o, h, l

                macdks, macdks60 = 0, 0
            else:
                if h > _h:
                    _h = h
                if l < _l:
                    _l = l
                if c > _m60:
                    macdks60 += 1
                macdks += 1
            if _yd > 1.5:
                ydd += 1
            elif _yd < -1.5:
                ydx += 1
            if _yd > 2:
                ydd2 += 1
            elif _yd < -2:
                ydx2 += 1
            if (o < c and o <= _m60 and c >= _m60) or (o > c and o >= _m60 and c <= _m60) or (clo_l[-2] > _m60 and c <= _m60) or (clo_l[-2] <= _m60 and c > _m60):
                macdr,macdg = 0, 0
        n = (str(t), o, h, l, c, v)

    return res



def highOpenSingle(types='sql',st='2018-08-01',et='2018-08-12'):
    """ 高开50个点以上第二波绿区做空，到60均线平仓，收益率统计 """
    short, long, phyd = 12, 26, 9
    if types == 'sql':
        data = sql_data(st,et)
        n = next(data)
    else:
        data = MongoDBData('HKFuture', 'future_1min').get_hsi(st, et)
        n = next(data)
    clo_l = [n[4]]
    ope_l = [n[1]]
    g, d = [], []
    sg, sd = 0, 0
    dc = [{}]  # deque()
    res = [['日期','开始时间','结束时间', '高低开多少点', 'macd波数', 'macd波数概率','正向异动', '反向异动','回调60均线空间','做空盈亏','最大亏损']]
    macds, ydd, ydx = 0, 0, 0  # macd个数，阳异动个数，阴异动个数
    wpy = defaultdict(int)
    jr = False
    ma60d = 0
    ma60d3 = 0
    ma60l = []
    macdl = []
    zuigaodian = 0
    kaishishijian = None
    for i, (t, o, h, l, c, v) in enumerate(data, 1):
        clo_l.append(c)
        ope_l.append(o)
        dc.append({'ema_short': 0, 'ema_long': 0, 'diff': 0, 'dea': 0, 'macd': 0,
                   'var': 0,  # 方差
                   'std': 0,  # 标准差
                   'mul': 0,  # 异动
                   })
        if i == 1:
            dc[i]['ema_short'] = clo_l[-2] + (c - clo_l[-2]) * 2 / short
            dc[i]['ema_long'] = clo_l[-2] + (c - clo_l[-2]) * 2 / long
            # dc[i]['ema_short'] = sum([(short-j)*da[i-j][4] for j in range(short)])/(3*short)
            # dc[i]['ema_long'] = sum([(long-j)*da[i-j][4] for j in range(long)])/(3*long)
            dc[i]['diff'] = dc[i]['ema_short'] - dc[i]['ema_long']
            dc[i]['dea'] = dc[i]['diff'] * 2 / phyd
            dc[i]['macd'] = 2 * (dc[i]['diff'] - dc[i]['dea'])

            # co = 1 if dc[i]['macd'] >= 0 else 0
        else:
            dc[i]['ema_short'] = dc[i - 1]['ema_short'] * (short - 2) / short + c * 2 / short
            dc[i]['ema_long'] = dc[i - 1]['ema_long'] * (long - 2) / long + c * 2 / long
            dc[i]['diff'] = dc[i]['ema_short'] - dc[i]['ema_long']
            dc[i]['dea'] = dc[i - 1]['dea'] * (phyd - 2) / phyd + dc[i]['diff'] * 2 / phyd
            dc[i]['macd'] = _macd = 2 * (dc[i]['diff'] - dc[i]['dea'])

            macdl.append(1) if _macd>0 else macdl.append(0)

        if i >= 60:
            ma = 60
            std_pj = sum(clo_l[i - j] - ope_l[i - j] for j in range(ma)) / ma
            dc[i]['var'] = sum((clo_l[i - j] - ope_l[i - j] - std_pj) ** 2 for j in range(ma)) / ma  # 方差 i-ma+1,i+1
            dc[i]['std'] = dc[i]['var'] ** 0.5  # 标准差
            dc[i]['mul'] = _yd = round((c - o) / dc[i]['std'], 2)

            _m60 = round(sum(j for j in clo_l[i - 59:i + 1]) / 60)

            if c>_m60:
                ma60l.append(1)
            elif c<=_m60:
                ma60l.append(0)

        is915 = (t.hour == 9 and t.minute == 15)

        if is915:
            jr = True
            gdk = o - clo_l[-2]
            if gdk > 0:
                g.append(gdk)
                sg += gdk
            elif gdk < 0:
                d.append(-gdk)
                sd += -gdk

        if jr:
            
            if macdl[-1] != macdl[-2]:  # (dc[i]['macd'] > 0 and dc[i - 1]['macd'] <= 0) or (dc[i]['macd'] <= 0 and dc[i - 1]['macd'] > 0):
                macds += 1
                ma60d = c
                if macds >= 3 and dc[i]['macd']<=0 and ma60d3==0:
                    ma60d3 = c
                    kaishishijian = str(t)
            if _yd > 1.5:
                ydd += 1
            elif _yd < -1.5:
                ydx += 1

            if h> zuigaodian:
                zuigaodian = h

            if ma60d3 and ma60d3-c<=-100:
                jr = False
                t2 = str(t)
                wpy[macds] += 1
                if macds >= 3 and gdk>=50 and ma60d3!=0:
                    res.append([t2[:10],kaishishijian,t2, gdk, macds, wpy[macds], ydd, ydx, abs(ma60d-c), -50, ma60d3-zuigaodian])
                macds, ydd, ydx = 0, 0, 0
                ma60d3 = 0
                zuigaodian = 0
            elif not is915 and ma60l[-1]!=ma60l[-2]: # and ((clo_l[-2] > _m60 and c <= _m60) or (clo_l[-2] <= _m60 and c > _m60) or (clo_l[-3] > _m60 and c <= _m60) or (clo_l[-3] <= _m60 and c > _m60)):  # (o < c and o <= _m60 and c >= _m60) or (o > c and o >= _m60 and c <= _m60) or
                jr = False
                t2 = str(t)
                wpy[macds] += 1
                if macds >= 3 and gdk>=50 and ma60d3!=0:
                    res.append([t2[:10],kaishishijian,t2, gdk, macds, wpy[macds], ydd, ydx, abs(ma60d-c), ma60d3-c, ma60d3-zuigaodian])

                macds, ydd, ydx = 0, 0, 0
                ma60d3 = 0
                zuigaodian = 0

    return res


if __name__ == '__main__':
    # res = highLowOpen('mongodb',st='2011-01-01',et='2018-09-12')
    # res = abnormal('mongodb',st='2011-01-01',et='2018-09-12')
    res = highOpenSingle('mongodb',st='2011-01-01',et='2018-09-12')
    for i in res[:5]:
        print(i)

    res = pd.DataFrame(res[1:],columns=res[0])

    res.to_pickle('highOpenSingle.pick')  # highLowOpen.pick

