import requests, re, datetime
import pyquery
import time
import logging


log_filename='logging.log'
log_format='%(filename)s[%(asctime)s][%(levelname)s]：%(message)s'
logging.basicConfig(filename=log_filename,filemode='a',level=logging.DEBUG,format=log_format,datefmt='%Y-%m-%d %H:%M:%S' )

class Future:
    def formatDate(self, Date):
        '''格式化日期时间05/01/2018 14:41为：datetime类型'''
        Date = re.split('[/ :]', Date)
        Date = Date[2] + Date[1] + Date[0] + Date[3] + Date[4]
        return datetime.datetime.strptime(Date, '%Y%m%d%H%M')

    def get_price(self, par):
        '''
        恒生指数期货实时行情数据,
        返回类型为以参数为Key，
        价格与时间组成list为value的字典
        '''
        # 返回结果字典，参数列表，错误提示

        rsp, error = {}, '参数：%s 错误！'
        months = {'F': '01', 'G': '02', 'H': '03', 'J': '04', 'K': '05', 'M': '06',
                  'N': '07', 'Q': '08', 'U': '09', 'V': '10', 'X': '11', 'Z': '12'}
        prods = ('HSI', 'MHI', 'HHI', 'MCH')
        nf = ('6', '7', '8', '9')
        prod = par[:3]
        month = par[3]
        year = par[4:]

        if prod not in prods:
            logging.error(error % prod)
            return

        if month not in months:
            logging.error(error % month)
            return

        if year not in nf:
            logging.error(error % year)
            return

        url = 'http://www.etnet.com.hk/www/tc/futures/index.php?subtype=%s&month=201%s%s' % (prod, year, months[month])
        s = requests.get(url).text
        s = s.replace('\t', '').replace('\n', '').replace('\r', '')
        patter = (
            'height="26" align="top"><span class="up">(\d+,\d+)</span></div>',
            '<div class="DivBoxStyleD" style="width:673px;">.*?(\d{2}/\d{2}/\d{4} \d{2}:\d{2})</td></tr></table>.*?'
        )
        # 价格
        s1 = re.findall(patter[0], s)[0]
        # 时间
        s2 = re.findall(patter[1], s)[0]
        rsp[par] = [float(s1.replace(',', ''))] + [self.formatDate(s2)]

        return rsp

    def get_F8(self):
        url='https://cn.investing.com/indices/hong-kong-40-futures'
        headers = {
            'Host': 'cn.investing.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0',
        }
        s = requests.get(url,headers=headers)
        print(s)
        pq = pyquery.PyQuery(s.text)
        price=pq('#last_last').text()
        price=price.replace(',','')
        times=pq('.bold.pid-8984-time').text()

        return times,price


if __name__ == '__main__':
    logging.info('开始...')
    fu = Future()
    param = 'HSIF8'
    s=fu.get_price(param)
    logging.info(s)
    print(s)
    #print(fu.get_F8())

