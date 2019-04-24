import requests
import os
import time
import datetime
import MyUtil


"""
一、获取股票市场上所有涨停的股票
二、保存当天的涨停股票到数据库
"""


class Limit_up:
    def __init__(self):
        '''初始化，从数据库更新所有股票代码'''
        self.cdate = datetime.datetime(*time.localtime()[:3])  # 当前日期
        try:
            self.conn = MyUtil.get_conn('stock_data')
            cur = self.conn.cursor()
        except Exception as exc:
            print(exc)
        time1 = -1
        # 获取存储股票代码文件的修改时间
        if os.path.isfile('codes_gp.txt'):
            times = os.path.getmtime('codes_gp.txt')
            time1 = time.localtime(times)[2]
        # 若不是在同一天修改的，则重新写入
        if time.localtime()[2] is not time1:
            cur.execute('select bazaar,code from stock_code where bazaar in ("sz","sh")')
            codes = cur.fetchall()
            # 获取股票代码
            codes = [i for i in codes if i[1][:3] in ('600', '000', '300', '601', '002', '603')]
            su = 1
            with open('codes_gp.txt', 'w') as f:
                for i in codes:
                    f.write(i[0] + i[1])
                    su += 1
                    if su % 600 == 0:
                        f.write('\n')
                    else:
                        f.write(',')
        self.codes = []
        try:
            with open('codes_gp.txt', 'r') as f:
                self.codes = f.readlines()
        except Exception as exc:
            print(exc)

    def insert_sql(self, datas):
        '''保存到数据库'''
        cur = self.conn.cursor()
        # 股票代码，中文名，开盘，最高，最低，收盘，成交额，成交量，昨日收盘，涨停时间，当前是否涨停，创建时间
        cur.execute('select code,createDate from stock_up')
        scode = cur.fetchall()
        for data in datas:
            try:
                if tuple([data[0], data[-1]]) not in scode:
                    sql = 'insert into stock_up values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
                    cur.execute(sql, (
                    data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10],
                    data[11]))
                else:
                    sql = 'update stock_up set high=%s,low=%s,close=%s,amount=%s,vol=%s,up_present=%s WHERE code="%s" AND createDate="%s"'
                    cur.execute(sql % (data[3], data[4], data[5], data[6], data[7], data[10], data[0], data[-1]))
            except Exception as exc:
                print(exc)

        self.conn.commit()

    def f_date(self, s_date):
        '''格式化日期时间，格式：20180103151743'''
        y = int(s_date[:4])
        m = int(s_date[4:6]) if int(s_date[4]) > 0 else int(s_date[5])
        d = int(s_date[6:8]) if int(s_date[6]) > 0 else int(s_date[7])
        h = int(s_date[8:10]) if int(s_date[8]) > 0 else int(s_date[9])
        M = int(s_date[10:12]) if int(s_date[10]) > 0 else int(s_date[11])
        return datetime.datetime(y, m, d, h, M)

    def read_code(self):
        codes = self.codes
        rou = lambda f: round((f * 1.1) - f, 2)
        #while 1:
        stock_up = []
        for code in codes:
            html = requests.get('http://qt.gtimg.cn/q=%s' % code).text
            html = html.replace('\n', '').split(';')
            html = [i.split('~') for i in html[:-1]]
            html = [i for i in html if 0 < float(i[3])]
            html = [[i[0][2:10],  # 市场加代码
                     i[1],  # 中文名称
                     float(i[5]),  # 开盘价
                     float(i[33]),  # 最高价
                     float(i[34]),  # 最低价
                     float(i[3]),  # 收盘价
                     float(i[37]),  # 成交额（万）
                     float(i[36]),  # 成交量（手）
                     float(i[4]),  # 昨日收盘价
                     self.f_date(i[30]),  # 涨停时间
                     1 if float(i[31]) >= rou(float(i[4])) else 0,  # 当前是否涨停(1是，0否)
                     self.cdate  # 创建的日期
                     ] for i in html
                    if round((float(i[33]) - float(i[4])) / float(i[4]), 2) >= 0.1]  # 计算是否涨停
            stock_up += html
        statistics = [i[1] for i in stock_up if i[10] > 0]
        print(len(stock_up), len(statistics), statistics)
        #self.insert_sql(stock_up)
        #    time.sleep(50)


if __name__ == '__main__':
    limit = Limit_up()
    limit.read_code()
    limit.conn.close()
