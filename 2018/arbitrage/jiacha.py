import datetime
import pandas as pd

"""
价差空间统计：
"""


def caches(func):
    """ 缓存方法 """
    cache_dict = {}

    def cac(*args, **kwargs):
        key = f'{func.__name__}{args}{kwargs}'
        if key not in cache_dict:
            cache_dict[key] = func(*args, **kwargs)
        return cache_dict[key]

    return cac


@caches
def last_dt(dt):
    """ 以当当前日期返回上一日日期 """
    d = datetime.datetime.strptime(dt, '%Y%m%d') - datetime.timedelta(days=1)
    return datetime.datetime.strftime(d, '%Y%m%d')


@caches
def is_dangyue(list_hsi, len_hsi, dt):
    """ 验证这一条数据不属于当前月的最后一天 """
    # list_hsi.index('20110209')
    ind = list_hsi.index(dt)
    if ind < len_hsi - 1:
        return list_hsi[ind + 1][:6] == dt[:6]
    return False


class Jiacha:

    def __init__(self, hsi='hsi.csv', hsi_day='HSI_day.csv'):
        hsi = pd.read_csv(hsi)
        self.hsi = hsi.sort_values('datetime')
        hsi_day = pd.read_csv(hsi_day, encoding='gbk')

        # 当月合约与日期为键，5分位、10分位、50分位、90分位、95分位为值保存字典
        self.hsi_dict = {f'{i[3]}': [i[7], i[8], i[10], i[12], i[13]] for i in hsi_day.values}

    def plan1(self, hsi, hsi_dict):
        """ 方案一：
            价差空间统计：
            从当前合约开始，统计当前合约与下月合约的价差；
            若当前秒的价差跌破上一日的10分位数，则买入；若达到上一日的50分位则卖出。
            若当前秒的价差突破上一日的90分位数，则卖出；若达到上一日的50分位则买入。
            在合约的末端强制平仓
        """
        hsi_values = hsi.values
        len_hsi_values = len(hsi_values)
        list_hsi = list(set(str(i[3])[:8] for i in hsi_values))
        list_hsi.sort()
        zuihou = {list_hsi[i] for i in range(len(list_hsi) - 1) if list_hsi[i][:6] != list_hsi[i + 1][:6]}  # 合约末日
        zuihou.add(list_hsi[-1])
        res = []  # 买卖记录集

        first = dict()  # 用来判断是否是开盘第一分钟
        first_hour = set()

        for j, i in enumerate(hsi_values):
            i3 = str(i[3])
            i38 = i3[:8]
            if i38 not in first:
                first[i38] = i3[:12]
            if j < len_hsi_values - 1 and str(hsi_values[j + 1][3])[8:10] >= '17':
                first_hour.add(i3)

        first = set(first.values())

        for j, i in enumerate(hsi_values):
            dt = str(i[3])
            ls_dt = last_dt(dt[:8])
            if ls_dt in hsi_dict and j < len_hsi_values - 1:
                f5, f10, f50, f90, f95 = hsi_dict[ls_dt]
                if dt[:8] not in zuihou and dt[:12] not in first:  # and dt not in first_hour:
                    # ['当月合约', '次月合约', '时间', '价差', '上日10分位', '上日50分位', '上日90分位', '操作']
                    # B：买，S：卖，Sc：平买，Bc：平卖，Sl、Bl：平本合约尾单买、卖
                    if res:
                        if i[4] >= f50 and res[-1][-1] == 'B':
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Sc'))
                        elif i[4] <= f50 and res[-1][-1] == 'S':
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Bc'))
                        elif i[4] <= f10 and res[-1][-1] != 'B':
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'B'))
                        elif i[4] >= f90 and res[-1][-1] != 'S':
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'S'))
                    else:
                        if i[4] <= f10:
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'B'))
                        elif i[4] >= f90:
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'S'))
                elif len(res) % 2:
                    # i = hsi_values[j-1]
                    res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Bl' if res[-1][-1] == 'S' else 'Sl'))
            elif len(res) % 2:
                res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Bl' if res[-1][-1] == 'S' else 'Sl'))

        return res

    def plan2(self, hsi, hsi_dict):
        """ 方案二：
            价差空间统计：
            从当前合约开始，统计当前合约与下月合约的价差；
            若当前秒的价差跌破上一日的10分位数，则买入；若达到上一日的50分位则卖出。
            若当前秒的价差突破上一日的90分位数，则卖出；若达到上一日的50分位则买入。
            在当天的末端强制平仓
        """
        hsi_values = hsi.values
        len_hsi_values = len(hsi_values)
        list_hsi = list(set(str(i[3])[:8] for i in hsi_values))
        list_hsi.sort()
        zuihou = {list_hsi[i] for i in range(len(list_hsi) - 1) if list_hsi[i][:6] != list_hsi[i + 1][:6]}  # 合约末日
        zuihou.add(list_hsi[-1])
        res = []  # 买卖记录集

        first = dict()  # 用来判断是否是开盘第一分钟
        first_hour = set()  # 用来判断是否是晚盘

        for j, i in enumerate(hsi_values):
            i3 = str(i[3])
            i38 = i3[:8]
            if i38 not in first:
                first[i38] = i3[:12]
            if j < len_hsi_values - 1 and str(hsi_values[j + 1][3])[8:10] >= '17':
                first_hour.add(i3)

        first = set(first.values())

        for j, i in enumerate(hsi_values):
            dt = str(i[3])
            ls_dt = last_dt(dt[:8])
            if ls_dt in hsi_dict and j < len_hsi_values - 1:
                f5, f10, f50, f90, f95 = hsi_dict[ls_dt]
                if dt[:8] not in zuihou and dt[:12] not in first and dt not in first_hour:
                    # ['当月合约', '次月合约', '时间', '价差', '上日10分位', '上日50分位', '上日90分位', '操作']
                    # B：买，S：卖，Sc：平买，Bc：平卖，Sl、Bl：平本合约尾单买、卖
                    if i[3] // 1000000 != hsi_values[j + 1][3] // 1000000:
                        if len(res) % 2:
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Bc' if res[-1][-1] == 'S' else 'Sc'))
                    elif res:
                        if i[4] >= f50 and res[-1][-1] == 'B':
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Sc'))
                        elif i[4] <= f50 and res[-1][-1] == 'S':
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Bc'))
                        elif i[4] <= f10 and res[-1][-1] != 'B':
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'B'))
                        elif i[4] >= f90 and res[-1][-1] != 'S':
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'S'))
                    else:
                        if i[4] <= f10:
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'B'))
                        elif i[4] >= f90:
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'S'))

                elif len(res) % 2:
                    # i = hsi_values[j-1]
                    res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Bl' if res[-1][-1] == 'S' else 'Sl'))
            elif len(res) % 2:
                res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Bl' if res[-1][-1] == 'S' else 'Sl'))

        return res

    def plan3(self, hsi, hsi_dict):
        """ 方案三：
            价差空间统计：
            从当前合约开始，统计当前合约与下月合约的价差；
            若当前秒的价差跌破上一日的5分位数，则买入；若达到上一日的50分位则卖出。
            若当前秒的价差突破上一日的95分位数，则卖出；若达到上一日的50分位则买入。
            在合约的末端强制平仓
        """
        hsi_values = hsi.values
        len_hsi_values = len(hsi_values)
        list_hsi = list(set(str(i[3])[:8] for i in hsi_values))
        list_hsi.sort()
        zuihou = {list_hsi[i] for i in range(len(list_hsi) - 1) if list_hsi[i][:6] != list_hsi[i + 1][:6]}  # 合约末日
        zuihou.add(list_hsi[-1])
        res = []  # 买卖记录集

        first = dict()  # 用来判断是否是开盘第一分钟
        first_hour = set()

        for j, i in enumerate(hsi_values):
            i3 = str(i[3])
            i38 = i3[:8]
            if i38 not in first:
                first[i38] = i3[:12]
            if j < len_hsi_values - 1 and str(hsi_values[j + 1][3])[8:10] >= '17':
                first_hour.add(i3)

        first = set(first.values())

        for j, i in enumerate(hsi_values):
            dt = str(i[3])
            ls_dt = last_dt(dt[:8])
            if ls_dt in hsi_dict and j < len_hsi_values - 1:
                f5, f10, f50, f90, f95 = hsi_dict[ls_dt]
                if dt[:8] not in zuihou and dt[:12] not in first:  # and dt not in first_hour:
                    # ['当月合约', '次月合约', '时间', '价差', '上日10分位', '上日50分位', '上日90分位', '操作']
                    # B：买，S：卖，Sc：平买，Bc：平卖，Sl、Bl：平本合约尾单买、卖
                    if res:
                        if i[4] >= f50 and res[-1][-1] == 'B':
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Sc'))
                        elif i[4] <= f50 and res[-1][-1] == 'S':
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Bc'))
                        elif i[4] <= f5 and res[-1][-1] != 'B':
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'B'))
                        elif i[4] >= f95 and res[-1][-1] != 'S':
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'S'))
                    else:
                        if i[4] <= f5:
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'B'))
                        elif i[4] >= f95:
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'S'))
                elif len(res) % 2:
                    # i = hsi_values[j-1]
                    res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Bl' if res[-1][-1] == 'S' else 'Sl'))
            elif len(res) % 2:
                res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Bl' if res[-1][-1] == 'S' else 'Sl'))

        return res

    def plan4(self, hsi, hsi_dict):
        """ 方案四：
            价差空间统计：
            从当前合约开始，统计当前合约与下月合约的价差；
            若当前秒的价差跌破上一日的5分位数，则买入；若达到上一日的50分位则卖出。
            若当前秒的价差突破上一日的95分位数，则卖出；若达到上一日的50分位则买入。
            在当天的末端强制平仓
        """
        hsi_values = hsi.values
        len_hsi_values = len(hsi_values)
        list_hsi = list(set(str(i[3])[:8] for i in hsi_values))
        list_hsi.sort()
        zuihou = {list_hsi[i] for i in range(len(list_hsi) - 1) if list_hsi[i][:6] != list_hsi[i + 1][:6]}  # 合约末日
        zuihou.add(list_hsi[-1])
        res = []  # 买卖记录集

        first = dict()  # 用来判断是否是开盘第一分钟
        first_hour = set()  # 用来判断是否是晚盘

        for j, i in enumerate(hsi_values):
            i3 = str(i[3])
            i38 = i3[:8]
            if i38 not in first:
                first[i38] = i3[:12]
            if j < len_hsi_values - 1 and str(hsi_values[j + 1][3])[8:10] >= '17':
                first_hour.add(i3)

        first = set(first.values())

        for j, i in enumerate(hsi_values):
            dt = str(i[3])
            ls_dt = last_dt(dt[:8])
            if ls_dt in hsi_dict and j < len_hsi_values - 1:
                f5, f10, f50, f90, f95 = hsi_dict[ls_dt]
                if dt[:8] not in zuihou and dt[:12] not in first and dt not in first_hour:
                    # ['当月合约', '次月合约', '时间', '价差', '上日10分位', '上日50分位', '上日90分位', '操作']
                    # B：买，S：卖，Sc：平买，Bc：平卖，Sl、Bl：平本合约尾单买、卖
                    if i[3] // 1000000 != hsi_values[j + 1][3] // 1000000:
                        if len(res) % 2:
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Bc' if res[-1][-1] == 'S' else 'Sc'))
                    elif res:
                        if i[4] >= f50 and res[-1][-1] == 'B':
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Sc'))
                        elif i[4] <= f50 and res[-1][-1] == 'S':
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Bc'))
                        elif i[4] <= f5 and res[-1][-1] != 'B':
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'B'))
                        elif i[4] >= f95 and res[-1][-1] != 'S':
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'S'))
                    else:
                        if i[4] <= f5:
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'B'))
                        elif i[4] >= f95:
                            res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'S'))

                elif len(res) % 2:
                    # i = hsi_values[j-1]
                    res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Bc' if res[-1][-1] == 'S' else 'Sc'))
            elif len(res) % 2:
                res.append((i[1], i[2], i[3], i[4], f10, f50, f90, 'Bc' if res[-1][-1] == 'S' else 'Sc'))

        return res

    def main(self, func):
        # 导入秒数据，与日统计数据

        res = func(self.hsi, self.hsi_dict)
        res2 = []  # 总盈亏统计
        # ('HSI1101', 'HSI1102', 20110104101754, -9.679, -8.333, -6.7, -5.111199999999998, 'B') res
        tj = {
            'b_vol': 0,  # 多单数量
            's_vol': 0,  # 空单数量
            'yl_vol': 0,  # 盈利数量
            'max_yl': None,  # 最大盈利
            'max_ks': None,  # 最大亏损
            'yl_total': 0,  # 盈利单的盈利总点数
            'ks_total': 0,  # 亏损单的亏损总点数
            'b_yl': 0,  # 盈利的多单数量
            's_yl': 0,  # 盈利的空单数量
            'yl_all': 0,  # 总盈利
        }
        for i in range(0, len(res), 2):
            if res[i][-1] == 'S':  # 空单
                yk = res[i][3] - res[i + 1][3]
                tj['s_vol'] += 1
                if yk > 0:
                    tj['yl_total'] += yk
                    tj['s_yl'] += 1
                    tj['yl_vol'] += 1
                else:
                    tj['ks_total'] += yk

            elif res[i][-1] == 'B':  # 多单
                yk = res[i + 1][3] - res[i][3]
                tj['b_vol'] += 1
                if yk > 0:
                    tj['yl_total'] += yk
                    tj['b_yl'] += 1
                    tj['yl_vol'] += 1
                else:
                    tj['ks_total'] += yk
            else:
                print('出现意外...', i, res[i])
                break
            if tj['max_yl'] is None:
                tj['max_yl'] = yk
            elif yk > tj['max_yl']:
                tj['max_yl'] = yk
            if tj['max_ks'] is None:
                tj['max_ks'] = yk
            elif yk < tj['max_ks']:
                tj['max_ks'] = yk
            tj['yl_all'] += yk

        vols = tj['b_vol'] + tj['s_vol']  # 总数量
        print(
            f'日期：{str(self.hsi.datetime[0])[:8]} -- {str(self.hsi.datetime[len(self.hsi)-1])[:8]}（{len(self.hsi_dict)} 天）')
        print('方法：')
        print(func.__doc__)
        print(f"""
    
        总共做单（买入卖出算一单）：{vols}
        盈利单数：{tj['yl_vol']}
        
        最大盈利：{round(tj['max_yl'],2)}
        最大亏损：{round(tj['max_ks'],2)}
        
        盈利的/平均每单盈利： {round(tj['yl_total'],2)}/{round(tj['yl_total']/tj['yl_vol'],2)}
        亏损的/平均每单亏损： {round(tj['ks_total'],2)}/{round(tj['ks_total']/(vols-tj['yl_vol']),2)}
        
        总盈亏： {round(tj['yl_all'],2)} 点
        总胜率： {round(tj['yl_vol']/vols*100,2)} %
        """)

        # for i in range(0, len(res), 2):
        #     res2.append(res[i][3] - res[i + 1][3] if res[i][-1] == 'S' else res[i + 1][3] - res[i][3])

    def tests(self, res):
        tj = {
            'b_vol': 0,  # 多单数量
            's_vol': 0,  # 空单数量
            'yl_vol': 0,  # 盈利数量
            'max_yl': None,  # 最大盈利
            'max_ks': None,  # 最大亏损
            'yl_total': 0,  # 盈利单的盈利总点数
            'ks_total': 0,  # 亏损单的亏损总点数
            'b_yl': 0,  # 盈利的多单数量
            's_yl': 0,  # 盈利的空单数量
            'yl_all': 0,  # 总盈利
        }
        for i in range(0, len(res), 2):
            if res[i][-1] == 'S':  # 空单
                yk = res[i][3] - res[i + 1][3]
                tj['s_vol'] += 1
                if yk > 0:
                    tj['yl_total'] += yk
                    tj['s_yl'] += 1
                    tj['yl_vol'] += 1
                else:
                    tj['ks_total'] += yk

            elif res[i][-1] == 'B':  # 多单
                yk = res[i + 1][3] - res[i][3]
                tj['b_vol'] += 1
                if yk > 0:
                    tj['yl_total'] += yk
                    tj['b_yl'] += 1
                    tj['yl_vol'] += 1
                else:
                    tj['ks_total'] += yk
            else:
                print('出现意外...', i, res[i])
                break
            if tj['max_yl'] is None:
                tj['max_yl'] = yk
            elif yk > tj['max_yl']:
                tj['max_yl'] = yk
            if tj['max_ks'] is None:
                tj['max_ks'] = yk
            elif yk < tj['max_ks']:
                tj['max_ks'] = yk
            tj['yl_all'] += yk

        vols = tj['b_vol'] + tj['s_vol']  # 总数量
        print(f"""
            日期：2011-01-03 -- 2018-08-30
            方法：
            从当前合约开始，统计当前合约与下月合约的价差；
            若当前秒的价差跌破上一日的10分位数，则买入；若达到上一日的50分位则卖出。
            若当前秒的价差突破上一日的90分位数，则卖出；若达到上一日的50分位则买入。
    
            总共做单（买入卖出算一单）：{vols}
            盈利单数：{tj['yl_vol']}
    
            最大盈利（点）：{round(tj['max_yl'],2)}
            最大亏损（点）：{round(tj['max_ks'],2)}
    
            盈利的/平均每单盈利（点）： {round(tj['yl_total'],2)}/{round(tj['yl_total']/tj['yl_vol'],2)}
            亏损的/平均每单亏损（点）： {round(tj['ks_total'],2)}/{round(tj['ks_total']/(vols-tj['yl_vol']),2)}
    
            总盈亏（点）： {round(tj['yl_all'],2)}
            总胜率： {round(tj['yl_vol']/vols*100,2)} %
            """)


if __name__ == '__main__':
    hsi = r'D:\tools\Tools\January_2019\2019-1-18\hsi.csv'
    hsi_day = r'D:\tools\Tools\January_2019\2019-1-18\HSI_day.csv'
    jc = Jiacha(hsi, hsi_day)
    res = jc.plan3(jc.hsi, jc.hsi_dict)
    jc.tests(res)
