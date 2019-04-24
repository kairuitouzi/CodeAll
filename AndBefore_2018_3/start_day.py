from struct import unpack
import os
from datetime import datetime
import importlib,asyncio
import threading
import MyUtil
#from concurrent import futures

#多线程的线程数量
thread_size = 40


def dateformat(a):
    '''日期格式化'''
    y = int(a / 10000)
    m = int((a % 10000) / 100)
    d = int((a % 10000) % 100)
    return datetime(y, m, d)


def day_csv_data(dirname, fname, sqls):
    '''数据的读取与插入'''
    code = fname.split('.')[0]
    conn = MyUtil.get_conn('stock_data')
    cur = conn.cursor()
    cur.execute(sqls[0] % code)
    conn.commit()
    isInsert = False
    try:
        last_date = cur.fetchone()[0]
    except:
        isInsert = True
        last_date = datetime(1990, 1, 1)
    if not last_date:
        last_date = datetime(1990, 1, 1)
    ofile = open(dirname + os.sep + fname, 'rb')
    e = -32
    while 1:
        try:
            ofile.seek(e, 2)  # 定位到最后一行
            buf = ofile.read()
            a = unpack('IIIIIfII', buf[0:32])
            dd = dateformat(a[0])
        except Exception as exc:
            print(exc)
            break
        if dd <= last_date:
            break
        openPrice = a[1] / 100.0
        high = a[2] / 100.0
        low = a[3] / 100.0
        close = a[4] / 100.0
        amount = a[5]
        vol = a[6]
        try:
            try:
                cur.execute(sqls[1], (dd, openPrice, high, low, close, amount, vol, code))
            except:
                conn.rollback()
                break
            if e >= -32:
                if isInsert:
                    insert_sql = 'INSERT INTO LAST_DATE(DATE,CODE) VALUES (%s,%s)'
                    cur.execute(insert_sql, (dd, code))
                else:
                    update_sql = 'UPDATE LAST_DATE SET DATE="%s" WHERE CODE="%s"'
                    cur.execute(update_sql % (dd, code))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            print('Error:', exc)
        e -= 32

    ofile.close()
    conn.close()
    print(fname)


def thread_func(path, file_name, x, sqls):
    '''多线程'''
    threads = [threading.Thread(target=day_csv_data, args=(path, i, sqls)) for i in file_name[x:x + thread_size]]
    for t in threads:
        t.setDaemon(True)
        t.start()
    for t in threads:
        t.join()


if __name__ == '__main__':
    '''执行入口'''
    path = ['D:\\新建文件夹\\vipdoc\sz\\lday', 'D:\\新建文件夹\\vipdoc\\sh\\lday', 'D:\\新建文件夹\\vipdoc\\ds\\lday']
    # path1 = 'D:\\同花顺软件\\同花顺\\history\\sznse\\day'
    try:
        for p in range(len(path)):
            x = 0
            sqls = ['SELECT DATE FROM LAST_DATE WHERE CODE="%s"',
                    'INSERT INTO transaction_data(date,open,high,low,close,amount,vol,code) values(%s,%s,%s,%s,%s,%s,%s,%s)']
            file_name = [i for i in os.listdir(path[p])]
            file_count = int(len(file_name) / thread_size) - 1
            file_yu = len(file_name) % thread_size
            for fn in range(file_count):
                thread_func(path[p], file_name, x, sqls=sqls)
                x += thread_size
            thread_func(path[p], file_name, x + file_yu, sqls=sqls)
    except Exception as exc:
        print(exc)
    finally:
        pass


