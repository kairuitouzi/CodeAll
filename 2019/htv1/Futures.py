import requests, re, time, datetime


class Future:

    def formatDate(self,Date):
        Date=re.split('[/ :]',Date)
        return Date[2]+Date[1]+Date[0]+Date[3]+Date[4]

    def get_price(self, par):
        '''
        恒生指数期货实时行情数据,
        返回类型为以参数为Key，
        价格与时间组成list为value的字典
        '''
        rsp = {}
        ps = [0, 0]
        if isinstance(par, str) and len(par) == 5:
            if par[:3] in ['HSI', 'MHI', 'HHI', 'MCH']:
                ps[0] = par[:3]
                if par[4] in ['6', '7', '8', '9']:  # 年份
                    ps[1] = par[4]
                    if par[3] == 'F':  # 1月
                        ps[1] += '01'
                    elif par[3] == 'G':  # 2月
                        ps[1] += '02'
                    elif par[3] == 'H':  # 3月
                        ps[1] += '03'
                    elif par[3] == 'J':  # 4月
                        ps[1] += '04'
                    elif par[3] == 'K':  # 5月
                        ps[1] += '05'
                    elif par[3] == 'M':  # 6月
                        ps[1] += '06'
                    elif par[3] == 'N':  # 7月
                        ps[1] += '07'
                    elif par[3] == 'Q':  # 8月
                        ps[1] += '08'
                    elif par[3] == 'U':  # 9月
                        ps[1] += '09'
                    elif par[3] == 'V':  # 10月
                        ps[1] += '10'
                    elif par[3] == 'X':  # 11月
                        ps[1] += '11'
                    elif par[3] == 'Z':  # 12月
                        ps[1] += '12'
                    else:
                        ps[1] = 0
                    if ps[1] is not 0:
                        url = 'http://www.etnet.com.hk/www/tc/futures/index.php?subtype=%s&month=201%s' % tuple(ps)
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
                    else:
                        print('参数：%s 错误！' % par[3:])
                        rsp = {}
                else:
                    print('参数：%s 错误！' % par[3:])
                    rsp = {}
            else:
                print('参数：%s 错误！' % par[:3])
                rsp = {}
        else:
            print('参数：%s 错误！' % par)
            rsp = {}

        return rsp



if __name__ == '__main__':
    fu = Future()
    h = ['HSI', 'MHI', 'HHI', 'MCH']
    d = [1, 2, 3, 6]
    print(fu.get_price('HSIF8'))
