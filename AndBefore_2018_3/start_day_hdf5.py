from struct import unpack
import os,h5py
from datetime import datetime
import importlib,asyncio
import numpy as np
import threading
#from concurrent import futures


thread_size=30


def dateformat(a):
    y = int(a / 10000)
    m = int((a % 10000) / 100)
    d = int((a % 10000) % 100)
    dt=y*100
    dt+=m
    dt*=100
    dt+=d
    return dt

f = h5py.File(r'D:\tools\Tools\stock_data.hdf5','w')
def day_csv_data(dirname, fname):
    ofile = open(dirname + os.sep + fname, 'rb')
    buf = ofile.read()
    e = 0
    result=[]
    while 1:
        try:
            a = unpack('IIIIIfII', buf[e:e+32])
            if not a:
                break
            dd = dateformat(a[0])
        except Exception as exc:
            print(exc)
            break
        
        openPrice = a[1] / 100.0
        high = a[2] / 100.0
        low = a[3] / 100.0
        close = a[4] / 100.0
        amount = a[5]
        vol = a[6]   
        e += 32
        #print(dd, openPrice, high, low, close, amount, vol,fname)
        result.append([dd, openPrice, high, low, close, amount, vol])


    #print(np.array(result))
    #f['/stock/%s' % fname[3:-4]]=result
    f['/stock/%s' % fname]=result
    ofile.close()
    print(fname)


def thread_func(path,file_name,x):
    threads = [threading.Thread(target=day_csv_data, args=(path, i)) for i in file_name[x:x + thread_size]]
    for t in threads:
        t.setDaemon(True)
        t.start()
    for t in threads:
        t.join()


if __name__=='__main__':
    path = ['D:\\新建文件夹\\vipdoc\sz\\lday', 'D:\\新建文件夹\\vipdoc\\sh\\lday']
    #path=[r'D:\新建文件夹\vipdoc\ds\lday']
    # path1 = 'D:\\同花顺软件\\同花顺\\history\\sznse\\day'
    try:
        for p in range(len(path)):
            x = 0
            file_name = [i for i in os.listdir(path[p])]
            file_count = int(len(file_name) / thread_size) - 1
            file_yu = len(file_name) % thread_size
            for fn in range(file_count):
                thread_func(path[p], file_name, x)
                x += thread_size
            thread_func(path[p], file_name, x + file_yu)
    except Exception as exc:
        print(exc)
    finally:
        f.close()



