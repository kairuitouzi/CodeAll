import time
import datetime
import random
import pandas as pd
from ib_insync import IB

class HS:
    def __init__(self):
        self.SXF = {"HSI":33.54, "MHI":13.6}  # 13.6
        self.hy = {"HSI":50, "MHI":10}   # 10
        
    def get_data(self, file_name=r'C:\Users\Administrator\Desktop\my2018\June_2018\2018-6-8\2018May25.txt'):
        dd = []
        for d in open(file_name, 'r'):
            d2 = d.split('\t')
            try:
                dd.append([int(d2[2]) if d2[2] else -int(d2[3]), float(d2[4]), d2[9], d2[0]])
            except Exception as exc:
                print(exc)
                continue
        d = pd.DataFrame(dd)
        d.columns = ['bs', 'price', 'time', 'code']
        return d

    def datas(self):
        data = {
            'jy': 0,  # 交易手数
            'price': 0,  # 交易价格
            'cb': 0,  # 总成本
            'jcb':0,  # 净会话成本
            'start_time': 0,  # 开始时间
            'end_time': 0,  # 结束时间
            'mai': 0,  # 买卖
            'kc': [],  # 开仓
            'all_kp': [],  # 当前会话所有开平仓
            'pcyl': 0,  # 平仓盈利
            'pcyl_all':0, # 平仓盈利汇总
            'all_price': 0,  # 叠加价格
            'all': 0,  # 总盈亏
            'sum_price': 0,  # 全天叠加价格
            'all_jy_add': 0,  # 全天所有交易手数，叠加
            'dbs':0,   # 序号
            'wcds1': 0,
            'wcds': 0,  # 完成的单
        }
        ind = 0
        _while = 0
        while 1:
            msg=yield data,ind
            hand = abs(msg[0])
            if _while <= 0 and hand > 1:
                _while = hand
            _while -= 1
            if _while <= 0:
                ind += 1
            data['price'] = msg[1]
            if data['jy'] == 0:
                data['pcyl'] = 0
                data['wcds1'] = 0
                data['pcyl_all'] = 0
                data['all_kp'] = []

                data['cb'] = 0  # 成本
                data['jcb'] = 0 # 净成本
                data['all_price'] = 0

            if msg[0]>0:
                data['jy'] += 1
                data['all_jy_add'] += 1
                data['mai'] = 1
                data['all_price'] += data['price']
                data['sum_price'] += data['price']
                data['kc'].append([1, data['price']])
                data['all_kp'].append([1, data['price']])

            elif msg[0]<0:
                data['jy'] -= 1
                data['all_jy_add'] += 1
                data['mai'] = -1
                data['all_price'] -= data['price']
                data['sum_price'] -= data['price']
                data['kc'].append([-1, data['price']])
                data['all_kp'].append([-1, data['price']])

            if len(data['kc']) > 1 and data['kc'][-1][0] != data['kc'][-2][0]:
                if data['kc'][-1][0] < 0:
                    data['pcyl'] = (data['kc'][-1][1] - data['kc'][-2][1])
                else:
                    data['pcyl'] = (data['kc'][-2][1] - data['kc'][-1][1])
                data['pcyl_all'] += data['pcyl']
                data['all'] += data['pcyl']
                data['kc'].pop()
                data['kc'].pop()
                data['wcds1'] += 1
                data['wcds'] += 1
            else:
                data['pcyl'] = 0

            if data['jy'] != 0:
                data['cb'] = data['all_price'] / data['jy']
                # jcbs = self.SXF * 2 / 50 * data['jy']
                jcbs = (data['wcds1'] + abs(data['jy'])) * self.SXF[msg[3][:3]] * 2 / self.hy[msg[3][:3]] / data['jy']
                #sum_cb = sum([cb[1] if cb[0]>0 else -cb[1] for cb in data['all_kp']]) # 净成本
                sum_cb = data['cb']+jcbs  # (sum_cb-jcbs)/data['jy']
                data['jcb'] = int(sum_cb) if data['jy']<0 else (int(sum_cb)+1 if sum_cb>int(sum_cb) else int(sum_cb))

            data['time'] = msg[2]


    def transfer(self,df):
        """ df:
                         bs    price                 time       code
                    0    -1   30934.0   2018/05/11 09:15:26     HSIK8
                    1    1   30941.0   2018/05/11 09:15:29      HSIK8
                    """
        res = []
        ind = 0
        is_ind = -1
        cbyl = 0
        dts = self.datas()
        dts.send(None)
        while ind < len(df.values):
            msg = df.values[ind]
            data, ind = dts.send(msg)
            pri = data['price']
            if len(data['kc']) > 0:
                yscb = round(sum(i[-1] for i in data['kc']) / len(data['kc']), 2)  # 原始成本
                cb = round(data['cb'], 2)  # 成本
            else:
                ak_k = [ak[1] for ak in data['all_kp'] if ak[0] > 0]
                ak_p = [ak[1] for ak in data['all_kp'] if ak[0] < 0]
                yscb = round(sum(ak_k) / len(ak_k), 2) if msg[0] < 0 else round(sum(ak_p) / len(ak_p), 2)
                cb = round(sum(ak_k) / len(ak_k), 2) if msg[0] > 0 else round(sum(ak_p) / len(ak_p), 2)

            jcb = data['jcb']  # 净成本
            cbyl += data['pcyl']  # 此笔盈利
            pjyl = round(data['all'] / data['wcds'], 2) if data['wcds'] > 0 else 0  # 平均盈利
            huihuapj = round(data['pcyl_all'] / data['wcds1'], 2) if data['wcds1'] > 0 else 0  # 会话平均盈利
            zcb = round(data['sum_price'] / data['jy'], 2) if data['jy'] != 0 else round(data['sum_price'], 2)  # 持仓成本
            jzcbs = (data['wcds'] + abs(data['jy'])) * self.SXF[msg[3][:3]] * 2 / self.hy[msg[3][:3]] / data['jy'] if data[
                                                                                                                  'jy'] != 0 else 0  # self.SXF * 2 / 50 * data['jy']
            jzcb = (data['sum_price'] / data['jy'] + jzcbs) if data['jy'] != 0 else 0  # 净持仓成本
            jzcb = int(jzcb) + 1 if jzcb > int(jzcb) else int(jzcb)

            jlr = round(data['all'] * self.hy[msg[3][:3]] - self.SXF[msg[3][:3]] * data['all_jy_add'], 2)  # 净利润
            jpjlr = round(jlr / data['wcds'], 2) if data['wcds'] > 0 else 0  # 净平均利润

            if ind != is_ind or (ind == is_ind and data['jy'] == 0):
                res.append(
                    [msg[3], data['time'], msg[0], pri, data['jy'], yscb, cb, jcb, cbyl, data['pcyl_all'], data['all'],
                     pjyl,
                     huihuapj, zcb, jzcb, data['all'] * self.hy[msg[3][:3]], jlr, jpjlr,
                     round(self.SXF[msg[3][:3]] * data['all_jy_add'], 2), data['wcds'], data['dbs']])
                cbyl = 0
            data['dbs'] += 1 if data['jy'] == 0 else 0  # 序号
            is_ind = ind
        return res

    def ray(self,df):
        res = []
        codes = set(df.iloc[:, 3])
        if len(codes)==1:
            res = self.transfer(df)
        else:
            for code in codes:
                df2 = df[df.iloc[:, 3] == code]
                rs = self.transfer(df2)
                res += rs

        columns = ['合约','时间','开仓', '当前价', '持仓','原始成本', '会话成本', '净会话成本', '此笔盈利', '会话盈利', '总盈利','总平均盈利','会话平均盈利','持仓成本','净持仓成本','利润','净利润','净平均利润','手续费','已平仓','序号']
        res = pd.DataFrame(res, columns=columns)
        return res



class HS2:
    _singleton = None
    ib = None

    def __new__(cls, *args, **kwargs):
        if not cls._singleton:
            cls._singleton = super(HS2,cls).__new__(cls, *args, **kwargs)
        return cls._singleton

    def __init__(self):
        # self.SXF = {"HSI": 19.04, "MHI": 13.6}  # 13.6
        # self.hy = {"HSI": 50, "MHI": 10}  # 10
        # try:
        #     if self.ib is None:
        #         self.ib = IB()
        #         # self.ib.connect('192.168.2.117', 7496, clientId=8, timeout=3)
        #         self.ib.connect('192.168.2.204', 7497, clientId=0, timeout=3)
        # except Exception as exc:
        #     self.ib = None
            # raise Exception(exc)
        pass


    def get_data(self):
        """ 获取交易记录 """
        if self.ib is None:
            return None

        # ib.trades()
        # ib.orders()
        # ib.fills()
        # util.startLoop()
        # hsi = Future?
        # hsi = Future('HSI', '201901')
        # ib.qualifyContracts(hsi)
        # hsi
        # ticker = ib.reqMktData(hsi)

        data = self.ib.fills()


        df = [[i.execution.shares if i.execution.side == 'BOT' else -i.execution.shares,
               i.execution.price,
               str(i.execution.time + datetime.timedelta(hours=8))[:19],
               i.contract.localSymbol,
               i.commissionReport.commission,
               int(i.contract.multiplier)] for i in data]

        df = pd.DataFrame(df, columns=['bs', 'price', 'time', 'code', 'sxf', 'hy'])

        return df

    def get_gd(self):
        """ 获取当前挂单的记录 """

        if self.ib is None:
            return []

        data = self.ib.openTrades()
        gd = [[i.contract.symbol, str(i.log[0].time + datetime.timedelta(hours=8))[:19],
               i.order.lmtPrice, i.order.action, i.order.totalQuantity, i.order.orderType]
              for i in data]

        gd = pd.DataFrame(gd, columns=['合约','时间','价格','买卖','数量','订单类型'])

        return gd

    def datas(self):
        data = {
            'jy': 0,  # 交易手数
            'price': 0,  # 交易价格
            'cb': 0,  # 总成本
            'jcb': 0,  # 净会话成本
            'start_time': 0,  # 开始时间
            'end_time': 0,  # 结束时间
            'mai': 0,  # 买卖
            'kc': [],  # 开仓
            'all_kp': [],  # 当前会话所有开平仓
            'pcyl': 0,  # 平仓盈利
            'pcyl_all': 0,  # 平仓盈利汇总
            'all_price': 0,  # 叠加价格
            'all': 0,  # 总盈亏
            'sum_price': 0,  # 全天叠加价格
            'all_jy_add': 0,  # 全天所有交易手数，叠加
            'dbs': 0,  # 序号
            'wcds1': 0,
            'wcds': 0,  # 完成的单
        }
        ind = 0
        _while = 0
        while 1:
            msg = yield data, ind
            hand = abs(msg[0])
            if _while <= 0 and hand > 1:
                _while = hand
            _while -= 1
            if _while <= 0:
                ind += 1
            data['price'] = msg[1]
            if data['jy'] == 0:
                data['pcyl'] = 0
                data['wcds1'] = 0
                data['pcyl_all'] = 0
                data['all_kp'] = []

                data['cb'] = 0  # 成本
                data['jcb'] = 0  # 净成本
                data['all_price'] = 0

            if msg[0] > 0:
                data['jy'] += 1
                data['all_jy_add'] += 1
                data['mai'] = 1
                data['all_price'] += data['price']
                data['sum_price'] += data['price']
                data['kc'].append([1, data['price']])
                data['all_kp'].append([1, data['price']])

            elif msg[0] < 0:
                data['jy'] -= 1
                data['all_jy_add'] += 1
                data['mai'] = -1
                data['all_price'] -= data['price']
                data['sum_price'] -= data['price']
                data['kc'].append([-1, data['price']])
                data['all_kp'].append([-1, data['price']])

            if len(data['kc']) > 1 and data['kc'][-1][0] != data['kc'][-2][0]:
                if data['kc'][-1][0] < 0:
                    data['pcyl'] = (data['kc'][-1][1] - data['kc'][-2][1])
                else:
                    data['pcyl'] = (data['kc'][-2][1] - data['kc'][-1][1])
                data['pcyl_all'] += data['pcyl']
                data['all'] += data['pcyl']
                data['kc'].pop()
                data['kc'].pop()
                data['wcds1'] += 1
                data['wcds'] += 1
            else:
                data['pcyl'] = 0

            if data['jy'] != 0:
                data['cb'] = data['all_price'] / data['jy']
                # jcbs = self.SXF * 2 / 50 * data['jy']
                jcbs = (data['wcds1'] + abs(data['jy'])) * msg[4] * 2 / msg[5] / data[
                    'jy']
                # sum_cb = sum([cb[1] if cb[0]>0 else -cb[1] for cb in data['all_kp']]) # 净成本
                sum_cb = data['cb'] + jcbs  # (sum_cb-jcbs)/data['jy']
                data['jcb'] = int(sum_cb) if data['jy'] < 0 else (
                    int(sum_cb) + 1 if sum_cb > int(sum_cb) else int(sum_cb))

            data['time'] = msg[2]

    def transfer(self, df):
        """ df:
                         bs    price                 time       code
                    0    -1   30934.0   2018/05/11 09:15:26     HSIK8
                    1    1   30941.0   2018/05/11 09:15:29      HSIK8
                    """
        res = []
        ind = 0
        is_ind = -1
        cbyl = 0
        dts = self.datas()
        dts.send(None)
        while ind < len(df.values):
            msg = df.values[ind]
            data, ind = dts.send(msg)
            pri = data['price']
            if len(data['kc']) > 0:
                yscb = round(sum(i[-1] for i in data['kc']) / len(data['kc']), 2)  # 原始成本
                cb = round(data['cb'], 2)  # 成本
            else:
                ak_k = [ak[1] for ak in data['all_kp'] if ak[0] > 0]
                ak_p = [ak[1] for ak in data['all_kp'] if ak[0] < 0]
                yscb = round(sum(ak_k) / len(ak_k), 2) if msg[0] < 0 else round(sum(ak_p) / len(ak_p), 2)
                cb = round(sum(ak_k) / len(ak_k), 2) if msg[0] > 0 else round(sum(ak_p) / len(ak_p), 2)

            jcb = data['jcb']  # 净成本
            cbyl += data['pcyl']  # 此笔盈利
            pjyl = round(data['all'] / data['wcds'], 2) if data['wcds'] > 0 else 0  # 平均盈利
            huihuapj = round(data['pcyl_all'] / data['wcds1'], 2) if data['wcds1'] > 0 else 0  # 会话平均盈利
            zcb = round(data['sum_price'] / data['jy'], 2) if data['jy'] != 0 else round(data['sum_price'],
                                                                                         2)  # 持仓成本
            jzcbs = (data['wcds'] + abs(data['jy'])) * msg[4] * 2 / msg[5] / data[
                'jy'] if data[
                             'jy'] != 0 else 0  # self.SXF * 2 / 50 * data['jy']
            jzcb = (data['sum_price'] / data['jy'] + jzcbs) if data['jy'] != 0 else 0  # 净持仓成本
            jzcb = int(jzcb) + 1 if jzcb > int(jzcb) else int(jzcb)

            jlr = round(data['all'] * msg[5] - msg[4] * data['all_jy_add'], 2)  # 净利润
            jpjlr = round(jlr / data['wcds'], 2) if data['wcds'] > 0 else 0  # 净平均利润

            if ind != is_ind or (ind == is_ind and data['jy'] == 0):
                res.append(
                    [msg[3], data['time'], msg[0], pri, data['jy'], yscb, cb, jcb, cbyl, data['pcyl_all'],
                     data['all'],
                     pjyl,
                     huihuapj, zcb, jzcb, data['all'] * msg[5], jlr, jpjlr,
                     round(msg[4] * data['all_jy_add'], 2), data['wcds'], data['dbs']])
                cbyl = 0
            data['dbs'] += 1 if data['jy'] == 0 else 0  # 序号
            is_ind = ind
        return res

    def ray(self, df):
        res = []
        codes = set(df.iloc[:, 3])
        if len(codes) == 1:
            res = self.transfer(df)
        else:
            for code in codes:
                df2 = df[df.iloc[:, 3] == code]
                rs = self.transfer(df2)
                res += rs

        columns = ['合约', '时间', '开仓', '当前价', '持仓', '原始成本', '会话成本', '净会话成本', '此笔盈利', '会话盈利', '总盈利', '总平均盈利', '会话平均盈利',
                   '持仓成本', '净持仓成本', '利润', '净利润', '净平均利润', '手续费', '已平仓', '序号']
        res = pd.DataFrame(res, columns=columns)
        return res


if __name__ == "__main__":
    h = HS()
    dd=h.get_data(r'C:\Users\Administrator\Desktop\my2018\June_2018\2018-6-8\2018May25.txt')  # 2018May2.txt  2018May11.txt
    res=h.ray(dd)
    print(res)
    import os
    if os.path.isfile('a.xls'):
        os.remove('a.xls')
    res.to_excel('a.xls')

