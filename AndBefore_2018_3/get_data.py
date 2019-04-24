import requests
import re
import pymysql
import time
import datetime

from langconv import *
import MyUtil

# 转换繁体到简体
def cht_to_chs(line):
    line = Converter('zh-hans').convert(line)
    line.encode('utf-8')
    return line
 


def get_data(url=None):
    '''获取恒生指数成分股数据，格式为：
    [(34, '腾讯控股'), (27, '香港交易所'), (21, '建设银行'), (18, '中国银行'), (16, '工商银行')...]'''
    weight_stock = [
        '汇丰控股', '腾讯控股', '友邦保险', '建设银行', '中国移动', '中国平安', '工商银行', '中国海洋石油', 
        '中国银行', '香港交易所', '长和', '中国石油化工股份', '中电控股', '领展房产基金', '恒生银行', '长实集团', 
        '新鸿基地产', '香港中华煤气', '中银香港', '中国石油股份', '中国人寿', '银河娱乐', '中国海外发展', 
        '金沙中国有限公司', '吉利汽车', '电能实业', '华润置地', '申洲国际', '碧桂园', '蒙牛乳业', '中信股份', 
        '石药集团', '新世界发展', '舜宇光学科技', '港铁公司', '中国神华', '九龙仓置业', '瑞声科技', '中国联通', 
        '恒基地产', '恒安国际', '中国生物制药', '交通银行', '万洲国际', '太古股份公司Ａ', '长江基建集团', 
        '信和置业', '中国旺旺', '恒隆地产', '华润电力']

    '''weight_stock=['中電控股', '九龍倉置業', '香港交易所', '中國石油股份', '中國石油化工股份', '東亞銀行',
       '碧桂園', '建設銀行', '萬洲國際', '恒基地產', '中國神華', '中國銀行', '滙豐控股', '中國平安',
       '招商局港口', '香港中華煤氣', '舜宇光學科技', '銀河娛樂', '聯想集團', '中信股份', '信和置業',
       '長實集團', '新鴻基地產', '領展房產基金', '華潤電力', "太古股份公司'A'", '中國聯通', '中國移動',
       '恒安國際', '恒生銀行', '長江基建集團', '友邦保險', '騰訊控股', '蒙牛乳業', '恒隆地產', '中國旺旺',
       '吉利汽車', '中國海外發展', '中銀香港', '新世界發展', '瑞聲科技', '電能實業', '中國海洋石油',
       '長和', '華潤置地', '中國人壽', '交通銀行', '金沙中國有限公司', '工商銀行', '港鐵公司']'''
    

    url = url if url else 'https://www.hsi.com.hk/HSI-Net/HSI-Net?cmd=nxgenindex&index=00001&sector=00'
    req = requests.get(url).text
    req = re.sub('\s', '', req)
    # req=re.findall('<constituentscount="51">(.*?)</stock></constituents><isContingency>',req)
    com = re.compile('contribution="([+|-]*\d+)".*?<name>.*?</name>.*?<sname>(.*?)</sname></stock>')
    s = re.findall(com, req)
    # print(s)
    s = [(int(i[0]), i[1]) for i in s]
    result = []
    for w in weight_stock:
        sun = [i for i in s if i[1] == w]
        if len(sun) == 1:
            result.append(sun[0])
        elif len(sun) > 1:
            sun2 = [i for i in sun if i[0] != 0]
            if not sun2:
                sun2 = sun
            result.append(sun2[0])

    s2 = str(datetime.datetime.now())[:11]
    ti = re.findall('datetime="(.*?)"current', req)[0]
    if time.localtime().tm_mday!=int(ti[3:5]):
        return [],0
    s3 = s2 + ti[-8:]
    s3=datetime.datetime.strptime(s3.split('.')[0],'%Y-%m-%d %H:%M:%S')
    print(result)
    print(s3)
    if s3<datetime.datetime.now()-datetime.timedelta(minutes=10):
        return '',''
    return result, s3


conn = MyUtil.get_conn('stock_data')
cur = conn.cursor()


def insert_mysql(tm):
    result, times = get_data()
    if str(times)[-8:-3] == tm:
        return str(times)[-8:-3]
    for res in result:
        try:
            cur.execute('insert into weight(number,name,time) values(%s,%s,%s)', (res[0],res[1], times))  # cht_to_chs(res[1])
        except Exception as exc:
            print(exc)
    conn.commit()
    return str(times)[-8:-3]

if __name__ == '__main__':
    try:
        c=cur.execute('DELETE FROM weight WHERE TIME<"%s"'%str(datetime.datetime.now())[:10])
        print('清除历史记录：%d条'%c)
    except Exception as exc:
            print(exc)
    tm = ''
    while 1:
        try:
            
            times=time.localtime()
            afternoon_close=(times.tm_hour==16 and times.tm_min>9) or times.tm_hour>16
            if (times.tm_hour==12 and times.tm_min>=1) or afternoon_close:
                if afternoon_close:
                    print("不在时间范围内，10秒后将退出！")
                    time.sleep(8)
                    break
                continue
            
            if times.tm_hour>=10 or (times.tm_hour==9 and times.tm_min>=20):
                tm = insert_mysql(tm)
                
        except Exception as exc:
            print(exc)
        time.sleep(60)
        print(datetime.datetime.now())
    conn.close()
