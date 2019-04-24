from django.shortcuts import render
import pymysql, json
import numpy as np
from django.conf import settings
from django.core.cache import cache

PAGE_SIZE=27

# 从缓存读数据
def read_from_cache( user_name):
    key = 'user_id_of_' + user_name
    try:
        value = cache.get(key)
    except: value=None
    if value == None:
        data = None
    else:
        data = json.loads(value)
    return data


# 写数据到缓存
def write_to_cache( user_name, data):
    key = 'user_id_of_' + user_name
    try:
        cache.set(key, json.dumps(data), settings.NEVER_REDIS_TIMEOUT)
    except Exception as exc:
        print(exc)


def index(rq):
    return render(rq, 'index.html')


def stockData(rq):
    code = rq.GET.get('code')
    data = read_from_cache(code)
    if not data:
        #conn = pymysql.connect(db='stockDate', user='kairuitouzi', passwd='kairuitouzi',host='192.168.2.226')
        conn = pymysql.connect(db='stockDate', user='root', passwd='123456')
        cur = conn.cursor()
        cur.execute('select date,open,close,low,high from transaction_data WHERE code="%s" ORDER BY DATE' % code)
        data = np.array(cur.fetchall())
        conn.close()
        data[:, 0] = [i.strftime('%Y/%m/%d') for i in data[:, 0]]
        data=data.tolist()
        write_to_cache(code, data)

    return render(rq, 'stockData.html', {'data': json.dumps(data), 'code': code})


def stockDatas(rq):
    #conn = pymysql.connect(db='stockDate', user='kairuitouzi', passwd='kairuitouzi',host='192.168.2.226')
    conn = pymysql.connect(db='stockDate', user='root', passwd='123456')
    cur = conn.cursor()
    rq_code=rq.GET.get('code')
    if rq_code:
        cur.execute('select date,open,high,low,close,amout,vol,code from moment_hours WHERE amout>0 and code="%s"'%rq_code)
        data = np.array(cur.fetchall())
        data[:, 0] = [i.strftime('%Y-%m-%d') for i in data[:, 0]]
        data = data.tolist()
    else:
        try:
            curPage = int(rq.GET.get('curPage', '1'))
            allPage=int(rq.GET.get('allPage', '1'))
            pageType=rq.GET.get('pageType')
        except:
            curPage,allPage=1,1
        if curPage==1 and allPage==1:
            cur.execute('select COUNT(1) from moment_hours WHERE amout>0')
            count=cur.fetchall()[0][0]
            allPage=int(count/PAGE_SIZE) if count%PAGE_SIZE==0 else int(count/PAGE_SIZE)+1
        if pageType=='up':
            curPage-=1
        elif pageType=='down':
            curPage+=1
        if curPage<1:
            curPage=1
        if curPage>allPage:
            curPage=allPage
        data = read_from_cache('data_house'+str(curPage))
        if not data:
            cur.execute('select date,open,high,low,close,amout,vol,code from moment_hours WHERE amout>0 limit %s,%s' % (
                curPage - 1, PAGE_SIZE))
            data = np.array(cur.fetchall())
            data[:, 0] = [i.strftime('%Y-%m-%d') for i in data[:, 0]]
            data = data.tolist()
            write_to_cache('data_house'+str(curPage), data)

    conn.close()
    return render(rq, 'stockDatas.html', {'data': data,'curPage':curPage,'allPage':allPage})
