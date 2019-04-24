
import requests,json

""" 股票数据提取 """

def formats(data):
    '''把数据转换成Python对象（字典）'''
    try:
        data=json.loads(data.split('=',1)[1])
    except Exception as exc:
        #print(exc)
        data=data.split('=')
    return data

def read_changes(code):
    '''变动的数据'''
    data=requests.get('http://web.sqt.gtimg.cn/q=%s'%code).text
    return formats(data)


def read_mins(code,times=1,size=240):
    '''分钟数据，code=股票市场+代码（例）：sz000001，times=时间类型（默认为1，
    可选：{1分钟:1,5分钟:5,30分钟:30，1小时:60}），size=获取数据的条数（默认240）'''
    if times==1:  #1分钟
        data = requests.get('http://web.ifzq.gtimg.cn/appstock/app/minute/query?_var=min_data_%s&code=%s' % (code, code)).text
        data=formats(data)['data'][code]['data']['data']
    elif times==5:  #5分钟
        data=requests.get('http://ifzq.gtimg.cn/appstock/app/kline/mkline?param=%s,m5,,%s&_var=m5_today'%(code,size)).text
        try:
            data=formats(data)['data'][code]['m5']
        except: data=None
    elif times==30:  #30分钟
        data=requests.get('http://ifzq.gtimg.cn/appstock/app/kline/mkline?param=%s,m30,,%s&_var=m30_today' % (code, size)).text
        try:
            data = formats(data)['data'][code]['m30']
        except: data = None
    elif times==60:  #60分钟
        data = requests.get(
            'http://ifzq.gtimg.cn/appstock/app/kline/mkline?param=%s,m60,,%s&_var=m60_today' % (code, size)).text
        try:
            data = formats(data)['data'][code]['m5']
        except: data = None
    else:
        data=None
    return data


def read_days(code,days=1,size=240):
    '''日线数据，code=股票市场+代码（例）：sz000001，days=日期类型
    （默认一日，可选{日:1,周:7,月:30}，size=获取数据的条数（默认240）'''
    if days==1:
        data=requests.get('http://web.ifzq.gtimg.cn/appstock/app/kline/kline?_var=kline_dayqfq&param=%s,day,,,%s'%(code,size)).text
        data=formats(data)['data'][code]['day']
    elif days==7:
        data=requests.get('http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_weekqfq&param=%s,week,,,%s,qfq'%(code,size)).text
        try:
            data=formats(data)['data'][code]['qfqweek']
        except:
            data=formats(data)['data'][code]['week']
    elif days==30:
        data=requests.get('http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_monthqfq&param=%s,month,,,%s,qfq'%(code,size)).text
        try:
            data=formats(data)['data'][code]['qfqmonth']
        except:
            data=formats(data)['data'][code]['month']
    else:
        data=None

    return data

def read_year(code,years):
    '''年线数据，code=股票市场+代码（例）：sz000001，years=年数类型
    （默认一年，可选{1年:1，3年:3，5年:5}，size=获取数据的条数（默认240）'''
    if years==1:
        data=requests.get('http://web.ifzq.gtimg.cn/other/klineweb/klineWeb/weekTrends?code=%s&type=qfq&_var=trend_qfq'%code).text
        data=formats(data)
    elif years==3:
        pass
    elif years==5:
        pass
    else:
        data=None
    return data

def main():
    code = 'sz000001'
    #code='sz000001'
    data=read_changes(code)
    print(data[1].split('~')[3:6]) #输出变动的数据：当前价，昨日收盘价，今日开盘价

    data = read_mins(code,times=1)
    print(data) #输出1分钟数据

    data=read_days(code,days=7)
    print(data)  #输出日线数据


if __name__=='__main__':
    main()

