
import os,pymysql,shelve,threading
from datetime import datetime
from struct import unpack
from start_day import dateformat

thread_size=30

def day_csv_data(dirname, fname,sqls):
    conn = pymysql.connect(db='stockDate', user='root', passwd='123456')
    cur = conn.cursor()
    code = fname.split('.')[0]

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
        openPrice = a[1] / 100.0
        high = a[2] / 100.0
        low = a[3] / 100.0
        close = a[4] / 100.0
        amount = a[5]
        vol = a[6]/100.0
        update_sql = 'insert into last_date (date,code) values(%s,%s)'
        try:
            cur.execute(update_sql,(dd,code))
        except Exception as exc:
            print(exc)
        if dd and dd>datetime(1990,1,1):
            break
        e -= 32
    conn.commit()
    ofile.close()
    print(fname)

def thread_func(path,file_name,x,sqls):
    threads = [threading.Thread(target=day_csv_data, args=(path, i,sqls)) for i in file_name[x:x + thread_size]]
    for t in threads:
        t.setDaemon(True)
        t.start()
    for t in threads:
        t.join()


if __name__=='__main__':
    path = ['D:\\新建文件夹\\vipdoc\sz\\lday', 'D:\\新建文件夹\\vipdoc\\sh\\lday']
    # path1 = 'D:\\同花顺软件\\同花顺\\history\\sznse\\day'
    try:
        for p in range(len(path)):
            x = 0
            sqls = ['SELECT DATE FROM last_date WHERE CODE="%s"',
                    'insert into transaction_data(date,open,high,low,close,amout,vol,code) values(%s,%s,%s,%s,%s,%s,%s,%s)']
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