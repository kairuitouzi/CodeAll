import os
import sys
import datetime
import pandas as pd
"""
.txt 文件，交易的部分数据提取，并合并
"""
try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BASE_DIR = os.path.join(BASE_DIR, 'AndBefore_2018_3')
    sys.path.append(BASE_DIR)
    from MyUtil import get_conn
except:
    from conn import get_conn

def get_files(folder,suffix='.txt'):
    """ 获取文件列表 """
    files = os.listdir(folder)
    txts = [i for i in files if suffix in i]
    txts.sort()
    return txts

def hebing():
    folder = r'D:\tools\Tools\June_2018\2018-6-20\gx'
    txts = get_files(folder)
    res = []
    for txt in txts:
        with open(folder+'\\'+txt,'r') as f:
            d = f.readlines()
            '时间','合约', '买/卖', '投机/套保', '成交价', '手数', '成交额', '开/平'
        p = {}
        title = d[0].split()
        for i in range(len(title)):
            p['sj'] = i if '时间' in title[i] else p.get('sj')
            p['hy'] = i if '合约' in title[i] else p.get('hy')
            p['mm'] = i if '买' in title[i] else p.get('mm') # 买卖
            p['kp'] = i if '开' in title[i] else p.get('kp') # 开平
            p['jg'] = i if '成交价' in title[i] else p.get('jg')
            p['ss'] = i if ('手数' in title[i] or '成交量' in title[i]) else p.get('ss')
            p['sxf'] = i if '手续费' in title[i] else p.get('sxf')
        for line in d[1:]:
            v = line.split()
            isj = txt[:4]+'-'+txt[4:6]+'-'+txt[6:8]+' '
            try:
                sj = isj + v[p['sj']] if p['sj'] is not None else isj + '00:00:00'
                hy = v[p['hy']] if p['hy'] is not None else None
                mm = v[p['mm']] if p['mm'] is not None else None
                kp = v[p['kp']] if p['kp'] is not None else None
                jg = v[p['jg']] if p['jg'] is not None else None
                ss = v[p['ss']] if p['ss'] is not None else None
                sxf = v[p['sxf']] if p['sxf'] is not None else None
            except IndexError as exc:
                print('Error:',exc,v)
                continue
            res.append([sj,hy.upper(),mm,kp,float(jg.replace(',','')),int(ss),float(sxf)])
    return res

def to_sql(data,table):
    conn = get_conn('carry_investment')
    cur = conn.cursor()
    if table == 'gx_record':
        sql = "INSERT INTO gx_record(datetime,exchange,varieties,code,busi,kp,turnover,right,price,vol,cost,insure) " \
              "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        for r in data:
            dt = r[0][:4] + '-' + r[0][4:6] + '-' + r[0][6:8] + ' 00:00:00'
            try:
                cur.execute(sql,(dt,r[1],r[2],r[3],r[4],float(r[5]),int(r[6]),r[7],r[8],r[9],r[10],r[11]))
            except Exception as exc:
                print(exc)
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
                print(exc)
    conn.commit()
    conn.close()

def to_jy(files):
    with open(files,'r') as f:
        d = f.readlines()
    try:
        str_ind = d.index('出入金明细\n') + 2
        end_ind = d[str_ind:].index('-'*126+'\n') + str_ind
        crj = [i.split() for i in d[str_ind:end_ind]]
    except:
        crj = []

    try:
        str_ind = d.index('成交记录\n') + 2
        end_ind = d[str_ind:].index('-' * 126 + '\n') + str_ind
        cjjl = [i.split() for i in d[str_ind:end_ind]]
        #c = pd.DataFrame(cjjl[1:-1],columns=cjjl[0][:12])
    except:
        cjjl = []
    return crj,cjjl # 出入金，成交记录

def to_jys():
    folder = "\\\\192.168.2.226\\公共文件夹\\660900202549BILLS\\"
    txts = get_files(folder=folder)
    crjs, cjjls = [], []
    for t in range(len(txts)):
        crj, cjjl = to_jy(folder+txts[t])
        if crjs and crjs[0][0] != '发生日期':
            crjs.insert(0,crj[0])
        if cjjls and cjjls[0][0] != '成交日期':
            cjjls.insert(0,cjjl[0])
        crjs += crj[1:-1]
        cjjls += cjjl[1:-1]
    for i in crjs:
        print(i)
    k = {}
    k2 = {}
    for i in cjjls:
        k[i[3]] = 0
        k2[i[3]] = i[2]
        print(i)
    print(k)
    print(k2)
    to_sql(crjs[1:],table='gx_entry_exit')
    to_sql(cjjls[1:],table='gx_record')


from io import StringIO
import pandas as pd
import re

def get_transfer_cash(file):
    with open(file, 'r') as f:
        s = f.read()

    cash = re.findall(r'出入金明细\n-{126}\n([\s\S]*?)-[126]?',s)
    if cash:
        cash_io = StringIO(cash[0])
        df = pd.read_table(cash_io, sep='\s+', engine='python', skipfooter=1)
        return df

def get_trade_records(file):
    with open(file, 'r') as f:
        s = f.read()

    cash = re.findall(r'成交记录\n-{126}\n([\s\S]*?)-[126]?',s)
    if cash:
        cash_io = StringIO(cash[0])
        df = pd.read_table(cash_io, sep='\s+', engine='python', skipfooter=1)
        return df

if __name__ == '__main__':
    # res = hebing()
    # to_sql(res)
    # for i in res:
    #     print(i)
    #files = "\\\\192.168.2.226\\公共文件夹\\660900202549BILLS\\" #D660900202549.201703o.txt"
    #to_jy(files)
    to_jys()
    #print(get_transfer_cash("\\\\192.168.2.226\\公共文件夹\\660900202549BILLS\\D660900202549.201702o.txt"))
    #print(get_trade_records("\\\\192.168.2.226\\公共文件夹\\660900202549BILLS\\D660900202549.201702o.txt"))

