import threading
import MyUtil
THREAD_SIZE=20

'''
ac = 3.82
this_c = 3.65
n_c = 4.03

ema_short = ac + (this_c - ac) * 2 / 13
ema_long = ac + (this_c - ac) * 2 / 27
diff = ema_short - ema_long
dea = diff * 2 / 10
macd = 2 * (diff - dea)

ema_short1 = ema_short * 11 / 13 + n_c * 2 / 13
ema_long1 = ema_long * 25 / 27 + n_c * 2 / 27
diff1 = ema_short1 - ema_long1
dea1 = dea * 8 / 10 + diff1 * 2 / 10
macd1 = 2 * (diff1 - dea1)

print('MACD: %.5f' % macd, diff, dea)
print('MACD_next: %.5f' % macd1, diff1, dea1)
print('MACD_next: %.5f' % macd2, diff2, dea2)
'''

def func_macd(code):
    conn = MyUtil.get_conn('stockDate')
    cur = conn.cursor()
    cur.execute('select date,close from transaction_data where code="%s" order by date'%code)
    data = cur.fetchall()
    result = list()
    for i in range(1, len(data)):
        jg = dict()
        if i == 1:
            ac = data[i - 1][1]
            this_c = data[i][1]
            jg['ema_short'] = ac + (this_c - ac) * 2 / 13
            jg['ema_long'] = ac + (this_c - ac) * 2 / 27
            jg['diff'] = jg['ema_short'] - jg['ema_long']
            jg['dea'] = jg['diff'] * 2 / 10
            jg['macd'] = 2 * (jg['diff'] - jg['dea'])
        else:
            n_c = data[i][1]
            jg['ema_short'] = result[i - 2]['ema_short'] * 11 / 13 + n_c * 2 / 13
            jg['ema_long'] = result[i - 2]['ema_long'] * 25 / 27 + n_c * 2 / 27
            jg['diff'] = jg['ema_short'] - jg['ema_long']
            jg['dea'] = result[i - 2]['dea'] * 8 / 10 + jg['diff'] * 2 / 10
            jg['macd'] = 2 * (jg['diff'] - jg['dea'])
        jg['date'] = data[i][0]
        jg['close'] = data[i][1]
        result.append(jg)
        cur.execute('insert into macd(code_id,date,close,code,ema_short,ema_long,diff,dea,macd) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (i,jg['date'],jg['close'],code,jg['ema_short'],jg['ema_long'],jg['diff'],jg['dea'],jg['macd']))
    print(code)
    conn.commit()
    cur.close()
    conn.close()

def thread_func(codes):
    threads = [threading.Thread(target=func_macd, args=(i[0],)) for i in codes]
    for t in threads:
        t.setDaemon(True)
        t.start()
    for t in threads:
        t.join()

if __name__=='__main__':
    conn = MyUtil.get_conn('stockDate')
    cur = conn.cursor()
    cur.execute('select code from transaction_data group by code')
    codes=cur.fetchall()
    x=0
    for i in range(0,len(codes)+THREAD_SIZE,THREAD_SIZE):
        try:
            thread_func(codes[x:x+THREAD_SIZE])
        except Exception as exc:
            print(exc)
            break
        x+=THREAD_SIZE
    conn.close()