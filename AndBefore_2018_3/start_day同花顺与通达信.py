from struct import unpack
import os
from datetime import datetime
import MyUtil

conn = MyUtil.get_conn('stock_data')
cur = conn.cursor()


def day_csv_data(dirname, fname,code):
    ''' 读取通达信day数据 '''
    with open(dirname + os.sep + fname, 'rb') as f:
        buf = f.read()
    num = len(buf)
    no = num / 32
    b = 0
    e = 32

    for i in range(int(no)):
        a = unpack('IIIIIfII', buf[b:e])
        dd=datetime(int(a[0][:4]),int(a[0][4:6]),int(a[0][6:]))
        openPrice = a[1] / 100.0
        high = a[2] / 100.0
        low = a[3] / 100.0
        close = a[4] / 100.0
        amount = a[5]
        vol = a[6] / 100.0

        sql = 'insert into transaction_data(date,open,high,low,close,amout,vol,code) values(%s,%s,%s,%s,%s,%s,%s,%s)'
        cur.execute(sql, (dd, openPrice, high, low, close, amount, vol, code))  # 插入数据库


        b += 32
        e += 32
    ifile.close()


def day_csv_data_ths(dirname, fname, targetDir,write_sql=False):
    ''' 读取同花顺的day数据 '''
    ofile = open(dirname + os.sep + fname, 'rb')
    buf = ofile.read()
    ofile.close()
    ifile = open(targetDir + os.sep + fname + '.csv', 'w')
    no = unpack('I', buf[6:10])[0]
    b = unpack('h', buf[10:12])[0]
    size = unpack('h', buf[12:14])[0]
    l_count = unpack('h', buf[14:16])[0]

    print('总行数:', no, '开始处:', b, '单行长度:', size, '字段数:', l_count)
    linename = 'date,open,high,low,close,amout,vol\n'  # ,str07
    ifile.write(linename)
    for i in range(no):
        dd = dateformat(unpack('I', buf[b:b + 4])[0])  # 时间
        openPrice = unpack('h', buf[b + 4:b + 6])[0] * 0.001  # 开盘价
        high = unpack('h', buf[b + 8:b + 10])[0] * 0.001  # 最高价
        low = unpack('h', buf[b + 12:b + 14])[0] * 0.001  # 最低价
        close = unpack('h', buf[b + 16:b + 18])[0] * 0.001  # 收盘价
        amount = unpack('I', buf[b + 20:b + 24])[0]  # 成交额
        vol = unpack('I', buf[b + 24:b + 28])[0] * 0.01  # 成交量

        code = fname.split('.')[0]

        if i == 0:
            preClose = close
        # ratio = round((close - preClose) / preClose * 100, 2)
        # preClose = close
        line = dd + ',' + str(openPrice) + ',' + str(high) + ',' + str(low) + ',' + str(close) + ',' + str(
            amount) + ',' + str(vol) + '\n'
        ifile.write(line)
        b += size

    ifile.close()


if __name__ == '__main__':
    '''path is 通达信 path，path1 is 同花顺path.
    function day_csv_data is 通达信，function day_csv_data_ths is 同花顺
    '''
    path = r'D:\新建文件夹\vipdoc\sz\lday'
    path1 = r'D:\同花顺软件\同花顺\history\sznse\day'
    func_ths = day_csv_data

    for i in os.listdir(path):
        try:
            code = i.split('.')[0]
            func_ths(path, i,code)
        except Exception as e:
            print(e)
    conn.commit()
    cur.close()
    conn.close()
