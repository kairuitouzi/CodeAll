from sqlalchemy import create_engine,String
#from numba import jit
import tushare as ts
import pandas as pd
import pymysql
import configparser

pymysql.install_as_MySQLdb()
config=configparser.ConfigParser()
config.read('conf.conf')

class MyTushare:
    def get_engine(self):
        '''建立与本地数据库的连接'''
        engine = create_engine('mysql://%s:%s@%s/stock_data?charset=utf8'%(config['U']['us'],config['U']['ps'],config['U']['hs']))
        return engine

    def get_stocks(self):
        '''获取所有股票信息'''
        df = ts.get_stock_basics()
        return df

    def formatDate(self,Date, formatType='YYYYMMDD'):
        '''日期格式YYYYMMDD转为YYYY-MM-DD'''
        formatType = formatType.replace('YYYY', Date[0:4])
        formatType = formatType.replace('MM', Date[4:6])
        formatType = formatType.replace('DD', Date[-2:])
        return formatType

    def write_sql(self,df,engine):
        '''写入到数据库'''
        Code = df.index  # 所有股票代码
        for code in Code:
            # code='300455'
            date = df.ix[code]['timeToMarket']  # 上市日期YYYYMMDD
            date = self.formatDate(str(date), 'YYYY-MM-DD')  # 改一下格式
            dh = ts.get_k_data(code, start=date, end='2017-12-31')  # 不复权
            dg = ts.get_k_data(code, start=date, end='2017-12-31', autype='hfq')  # 后复权
            try:
                del dg['date']
                del dg['volume']
                del dg['code']
            except Exception as exc:
                print(exc)
            try:
                dg.rename(columns={'open': 'fopen', 'close': 'fclose', 'high': 'fhigh', 'low': 'flow'}, inplace=True)
                mergeColumn = pd.concat([dh, dg], axis=1)
                mergeColumn.to_sql('history', engine, if_exists='append',dtype={'date':String(10),'code':String(8)})
            except Exception as exc:
                print(exc)
            print(code)

if __name__=='__main__':
    tus=MyTushare()
    tus.write_sql(df=tus.get_stocks(),engine=tus.get_engine())