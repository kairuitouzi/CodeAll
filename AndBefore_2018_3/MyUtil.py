
import json
import re
import pymongo
import datetime
import math
import pymysql
import configparser

config=configparser.ConfigParser()
config.read(r'D:\tools\Tools\EveryDay\demo\AndBefore_2018_3\conf.conf')

def get_conn(dataName):
    return pymysql.connect(db=dataName,user=config['U']['us'],passwd=config['U']['ps'],host=config['U']['hs'],charset='utf8')

def closeConn(conn):
    conn.commit()
    conn.close()



def dtf(d):
    """ 日期时间格式化 """
    if isinstance(d, str):
        d = d.strip()
        if len(d) == 10:
            d = datetime.datetime.strptime(d, '%Y-%m-%d')
        else:
            d = datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
        return d
    elif isinstance(d, datetime.datetime):
        d = datetime.datetime.strftime(d, '%Y-%m-%d %H:%M:%S')
        return d
    elif isinstance(d, datetime.date):
        d = datetime.datetime.strftime(d, '%Y-%m-%d')
        return d


class MongoDBData:
    """ MongoDB 数据库的连接与数据查询处理类 """

    def __init__(self, db=None, table=None):
        self.db_name = db
        self.table = table
        # if not self._coll:
        #     self._coll = self.get_coll()
        self._coll = self.get_coll()

    def get_coll(self):
        client = pymongo.MongoClient('mongodb://192.168.2.226:27017')
        client.admin.authenticate(config['MONGODB']['us'], config['MONGODB']['ps'])
        self.db = client[self.db_name] if self.db_name else client['Future']
        coll = self.db[self.table] if self.table else self.db['future_1min']
        return coll

    def get_hsi(self, sd, ed, code='HSI'):
        """
        获取指定开始日期，结束日期，指定合约的恒指分钟数据
        :param sd: 开始日期
        :param ed: 结束日期
        :param code: 合约代码
        :return:
        """

        if isinstance(sd, str):
            sd = dtf(sd)
        if isinstance(ed, str):
            ed = dtf(ed)
        dates = set()
        start_dates = [sd]
        _month = sd.month
        _year = sd.year
        e_y = ed.year
        e_m = ed.month
        _while = 0

        while _year < e_y or (_year == e_y and _month <= e_m):
            _month = sd.month + _while
            _year = sd.year + math.ceil(_month / 12) - 1
            _month = _month % 12 if _month % 12 else 12
            code = code[:3] + str(_year)[2:] + ('0' + str(_month) if _month < 10 else str(_month))
            try:
                _ed = self.db['future_contract_info'].find({'CODE': code})[0]['EXPIRY_DATE']
            except:
                return
            if _ed not in start_dates:
                start_dates.append(_ed)
            _while += 1
            if sd >= _ed:
                continue
            _sd = start_dates[-2]

            if _sd > ed:
                return
            data = self._coll.find({'datetime': {'$gte': _sd, '$lt': _ed}, 'code': code},
                                   projection=['datetime', 'open', 'high', 'low', 'close', 'volume']).sort('datetime',
                                                                                                           1)  # 'HSI1808'

            _frist = True
            for i in data:
                date = i['datetime']
                if _frist:
                    _frist = False
                    exclude_time = str(date)[:10]
                    dates.add(datetime.datetime.strptime(exclude_time + ' 09:14:00', '%Y-%m-%d %H:%M:%S'))
                    dates.add(datetime.datetime.strptime(exclude_time + ' 12:59:00', '%Y-%m-%d %H:%M:%S'))
                if date not in dates:
                    dates.add(date)
                    if date > ed:
                        return
                    yield [date, i['open'], i['high'], i['low'], i['close'], i['volume']]

    def data_day(self, code, date):
        """ 获取一天的期货数据 """
        day = datetime.timedelta(days=1)
        data = self._coll.find({'datetime': {'$gte': date, '$lt': date + day}, 'code': code},
                               projection=['datetime', 'open', 'high', 'low', 'close', 'trade']).sort('datetime', 1)
        # 时间，开盘，收盘，最低，最高，成交量
        # data = [[i['datetime'], i['open'], i['close'], i['low'], i['high'], i['trade']] for i in data]
        # data.sort()
        # return data
        for i in data:
            yield [i['datetime'], i['open'], i['close'], i['low'], i['high'], i['trade']], i['datetime'].hour


def sql_data(st='2018-11-08', ed='2018-11-10'):
    sql = f"SELECT DATETIME,OPEN,high,low,CLOSE,vol FROM wh_same_month_min WHERE prodcode='HSI' AND DATETIME>='{st}' AND DATETIME<='{ed}' ORDER BY DATETIME"
    conn = pymysql.connect(db='carry_investment', user=config['U']['us'], passwd=config['U']['ps'], host='192.168.2.226',charset='utf8')
    cur = conn.cursor()
    cur.execute(sql)
    conn.close()
    data = cur.fetchall()
    for i in data:
        yield i

class MyUtil:
    def __init__(self):
        try:
            import redis
            pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
            self.r = redis.Redis(connection_pool=pool)  # 建立Redis连接(以连接池的方式)
        except:
            pass

    def getCode(self,rq_data):
        try:
            code_data=json.loads(self.r.get('stock_code'))
        except:
            conn=get_conn('stock_data')
            cur=conn.cursor()
            cur.execute('SELECT * FROM STOCK_CODE')
            code_data = cur.fetchall()
            conn.close()
            try:
                self.r.set('stock_code',json.dumps(code_data))
            except:
                pass
        res_data = [i for i in code_data if
                    rq_data in i[0] or rq_data in i[1] or rq_data in i[2] or (
                        rq_data in i[3] if i[3] else None) or rq_data in i[4]]
        try:
            for i in res_data:
                chd=i[0][:3]  #代码开头
                if chd=='600' or chd=='000' or chd=='300' or chd=='601' or chd=='002':
                    res_code=(i[-1]+i[0],i[1])
                    break
            else:
                for i in res_data:
                    if len(re.findall('\d',i[0]))>=5:
                        res_code=(i[-1]+i[0],i[1])
                        break
                    elif i[3]:
                        res_code = (i[-1] + i[3],i[1])
                        break
                else:    
                    res_code=None
        except:
            res_code=None
        return res_code


if __name__=='__main__':
    pass
