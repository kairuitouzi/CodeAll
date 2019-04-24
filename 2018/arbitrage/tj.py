import numpy as np
import pandas as pd

"""
获取计算好的恒指价差数据
计算：'当前合约', '次月合约', '日期', '平均值', '标准差', '总数', '10分位', '25分位', '50分位', '75分位', '90分位', '统计条数'

pandas 计算方法
data['date'] = data['datetime'].astype(str).str[:8]
grouped = data.groupby('date').spread
mean = grouped.mean()
quantile = grouped.quantile([0.25, 0.5, 0.75])
std = grouped.std()
"""


def get_data(path):
    """ 获取DataFrame数据 """
    data = pd.read_pickle(path)
    return data


def tjs(data):
    """ 按天统计下每天的均值，方差，以及25,50,75，3个百分位数 """
    dayd = []
    days = set()  # 日期列表
    for i in data.values:
        _day = i[2][:8]
        if _day not in days:
            days.add(_day)
            if dayd:
                # ['当前合约', '次月合约', '日期', '平均值', '标准差', '总数', '5分位', '10分位', '25分位', '50分位', '75分位', '90分位', '95分位', '统计条数']
                yield [*last_hy, last_day, np.average(dayd), np.std(dayd), sum(dayd), np.percentile(dayd, 5),
                       np.percentile(dayd, 10), np.percentile(dayd, 25), np.percentile(dayd, 50), 
                       np.percentile(dayd, 75),np.percentile(dayd, 90), np.percentile(dayd, 95), len(dayd)]
                dayd = []
        dayd.append(i[3])
        last_day = _day
        last_hy = [i[0], i[1]]


def main():
    codes = ['HSI', 'MHI', 'HHI']
    columns = ['当前合约', '次月合约', '日期', '平均值', '标准差', '总数', '5分位', '10分位', '25分位', '50分位', '75分位', '90分位', '95分位', '统计条数']
    for code in codes:
        path = r"D:\tools\Tools\January_2019\2019-1-18\data\%s.pkl" % code
        data = get_data(path)
        data = data.sort_values('datetime')
        hsi = [i for i in tjs(data)]
        hsi = pd.DataFrame(hsi, columns=columns)
        hsi.to_csv('%s_day.csv' % code)
