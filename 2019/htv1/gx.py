import os
import time
import random
import pandas as pd

from myconn import myconn

class HS:
    def __init__(self):
        self.SXF = {'bu1706': 0.0001, 'rb1705': 0.0001, 'ru1705': 0.000045, 'j1705': 0,
                    'ru1709': 0, 'j1709': 0, 'al1711': 0, 'rb1801': 0,
                    'j1801': 0, 'rb1805': 0, 'rb1810': 0, 'AP1810': 0, 'CF1901': 0}
        self.hy = {'bu1706': 10, 'rb1705': 10, 'ru1705': 10, 'j1705': 0,
                   'ru1709': 0, 'j1709': 0, 'al1711': 0, 'rb1801': 0,
                   'j1801': 0, 'rb1805': 0, 'rb1810': 0, 'AP1810': 0, 'CF1901': 0}
        self.code_name = {'bu1706': '石油沥青', 'rb1705': '螺纹钢', 'ru1705': '橡胶', 'j1705': '冶金焦炭',
                          'ru1709': '橡胶', 'j1709': '冶金焦炭', 'al1711': '铝', 'rb1801': '螺纹钢',
                          'j1801': '冶金焦炭', 'rb1805': '螺纹钢', 'rb1810': '螺纹钢', 'AP1810': '苹果',
                          'CF1901': '棉一号'}

    def get_data(self, file_name):
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

    def gx_lsjl(self,folder):
        data = pd.DataFrame()
        xls = [folder+os.sep+i for i in os.listdir(folder) if '.xls' in i]
        for i in xls:
            p = pd.read_excel(i)
            data = data.append(p)
            # data = pd.concat([data,p])
        return data

    def format_data(self,data):
        ds = []
        for i in data.values:
            bs = -i[5] if i[3] == '卖出' else i[5]
            price = i[6]
            sj = str(i[0])
            sj = sj[:4] + '/' + sj[4:6] + '/' + sj[6:] + ' ' + i[13]
            code = i[2]
            cost = i[7]
            ds.append([bs, price, sj, code, cost])
        ds = pd.DataFrame(ds,columns=['bs', 'price', 'time', 'code', 'cost'])
        return ds

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
            'cost': 0,  # 手续费
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
                data['cost'] += msg[4]

            elif msg[0] < 0:
                data['jy'] -= 1
                data['all_jy_add'] += 1
                data['mai'] = -1
                data['all_price'] -= data['price']
                data['sum_price'] -= data['price']
                data['kc'].append([-1, data['price']])
                data['all_kp'].append([-1, data['price']])
                data['cost'] += msg[4]

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
                jcbs = (data['wcds1'] + abs(data['jy'])) * data['cost'] / data['jy']
                # sum_cb = sum([cb[1] if cb[0]>0 else -cb[1] for cb in data['all_kp']]) # 净成本
                sum_cb = data['cb'] + jcbs  # (sum_cb-jcbs)/data['jy']
                data['jcb'] = int(sum_cb) if data['jy'] < 0 else (
                    int(sum_cb) + 1 if sum_cb > int(sum_cb) else int(sum_cb))

            data['time'] = msg[2]

    def transfer(self, df):
        """ df:
                         bs    price                 time       code     cost
                    0    -1   10055.0   2018/06/19 14:51:12     AP1810   10.18
                    1    -2   10032.0   2018/06/19 14:52:54     AP1810  10.18
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
            jzcbs = (data['wcds'] + abs(data['jy'])) * data['cost'] / data['jy'] if \
            data[
                'jy'] != 0 else 0  # self.SXF * 2 / 50 * data['jy']
            jzcb = (data['sum_price'] / data['jy'] + jzcbs) if data['jy'] != 0 else 0  # 净持仓成本
            jzcb = int(jzcb) + 1 if jzcb > int(jzcb) else int(jzcb)

            jlr = round(data['all'] - data['cost'], 2)  # 净利润
            jpjlr = round(jlr / data['wcds'], 2) if data['wcds'] > 0 else 0  # 净平均利润

            if ind != is_ind or (ind == is_ind and data['jy'] == 0):
                res.append(
                    [msg[3], data['time'], msg[0], pri, data['jy'], yscb, cb, jcb, cbyl, data['pcyl_all'], data['all'],
                     pjyl,
                     huihuapj, zcb, jzcb, data['all'], jlr, jpjlr,
                     round(data['cost'], 2), data['wcds'], data['dbs']])
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

def to_sql(data,table):
    conn = myconn.get_conn('carry_investment')
    cur = conn.cursor()
    if table == 'gx_record':
        sql = "INSERT INTO gx_record(datetime,exchange,code,busi,kp,price,vol,cost,insure) " \
              "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        for r in data.values:
            r[0] = str(r[0])
            dt = r[0][:4] + '-' + r[0][4:6] + '-' + r[0][6:8] + ' ' + str(r[13])
            try:
                cur.execute(sql,(dt,r[1],r[2],r[3],r[4],float(r[6]),int(r[5]),r[7],r[14]))
            except Exception as exc:
                pass # print(exc)
    if table == 'gx_entry_exit':
        sql = "INSERT INTO gx_entry_exit(datetime,type,out,enter,currency,bank,direction,abstract) " \
              "VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
        for r in data:
            dt = r[0][:4]+'-'+r[0][4:6]+'-'+r[0][6:8]+' 00:00:00'
            out = r[5] if r[4] == '出金' else 0
            enter = r[5] if r[4] == '入金' else 0
            currency = '人民币' if r[6] == '1' else None
            try:
                cur.execute(sql,(dt,r[1],out,enter,currency,r[3],r[4],r[7]+r[8]))
            except Exception as exc:
                pass # print(exc)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    h = HS()
    # dd = h.get_data(r'D:\tools\Tools\June_2018\2018-6-8\2018May25.txt')  # 2018May2.txt  2018May11.txt
    data = h.gx_lsjl(r'\\192.168.2.226\公共文件夹\gx\历史成交')
    data2 = h.gx_lsjl(r'\\192.168.2.226\公共文件夹\gx\出入金')
    dd = h.format_data(data)
    res = h.ray(dd)
    #to_sql(data,'gx_record')
    #print(len(data))
    #print(data2)
    # data['日期'] = data['日期'].map(lambda x: str(x)[:4]+'-'+str(x)[4:6]+'-'+str(x)[6:])
    # print(data)
    print(res)

    if os.path.isfile('a.xls'):
        os.remove('a.xls')
    res.to_excel('a.xls')

