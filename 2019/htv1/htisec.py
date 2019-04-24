import urllib3
import requests
import pandas as pd
import re
import time
import datetime
import pymongo as pm
import numpy as np
import configparser

from dateutil import parser
from pyquery import PyQuery as pq
from collections import defaultdict
from ib_insync import IB

class Hsi(object):
    '''HTISEC to Web Trade'''

    _singleton = None
    ib = None

    def __new__(cls, *args, **kwargs):
        if not cls._singleton:
            cls._singleton = super(Hsi, cls).__new__(cls, *args, **kwargs)
        return cls._singleton
    
    def __init__(self):
        urllib3.disable_warnings()
        self.status=0
        self.error=0

        #允许不止损的交易单数 
        self.nostop=0
        #默认止损的点数 
        self.stop_point=50

        # 是否去除不对应不全的交易记录
        self.is_clear = False

    def verify_error(self,html):
        '''检验是否有错误提示 '''
        reg=re.search(self.reg['error'] ,html.encode('utf-8'))
        if reg:
            self.error=reg.group(1).decode('utf-8')
            return 1
        else:
            return 0   

    # auto login
    def login_a(self):
        self.login(self.account['user'],self.account['pwd'])

    #log in
    # def login(self,user,pwd):
    #     '''auto login for htisec'''
    #     self.account={'user':user,'pwd':pwd}
    #     self._s.cookies.clear()
    #     try:
    #         get1=self._s.get(self.url['login_jsp'] ,verify=False)
    #         #print('Login Request Status:',get1.status_code)
    #         jid1=get1.cookies['JSESSIONID']
    #         self._headers['Cookie']="JSESSIONID="+jid1
    #         login_data = {'login_id': user, 'pwd': pwd}
    #         post1 = self._s.post(self.url['login_do'] , data=login_data,verify=False,timeout=5)
    #         if self.verify_error(post1.text):
    #             self.status=0
    #             print("Login Error:",self.error)
    #             return 0
    #         self._jid=post1.cookies.values()[0]
    #         self._headers['Cookie']="JSESSIONID="+self._jid
    #         print("Login OK,JSESSIONID:", self._jid)
    #         self.status=1
    #         self.login_time=time.time()
    #         print("Login Time:",time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    #         return self._jid
    #     except Exception as e:
    #         self.status=0
    #         print("Login Try_Error:",e)

    def login_1(self,user,pwd, clientId):
        ''' 登陆 '''
        # self.account={'user':user,'pwd':pwd}
        # self._s.cookies.clear()
        # #login jsp
        # get1 = self._s.get(self.url['login_jsp'], verify=False)
        # # print('Login Request Status:',get1.status_code)
        # jid1 = get1.cookies['JSESSIONID']
        # self._headers['Cookie'] = "JSESSIONID=" + jid1
        # login_data = {'login_id': user, 'pwd': pwd}
        # post1 = self._s.post(self.url['login_do'], data=login_data, verify=False, timeout=20)
        # print(post1.status_code)
        # self.login1_post=post1.text
        # return post1.text
        try:
            if self.ib is None:
                self.ib = IB()
                # self.ib.connect('192.168.2.117', 7496, clientId=8, timeout=3)
                self.ib.connect(user, pwd, clientId=clientId, timeout=3)
        except Exception as exc:
            self.ib = None
            # raise Exception(exc)
        return self.ib


    def get_tradelist(self):
        """ 获取交易记录 """
        if self.ib is None:
            return None

        # ib.trades()
        # ib.orders()
        # ib.fills()
        # util.startLoop()
        # hsi = Future?
        # hsi = Future('HSI', '201901')
        # ib.qualifyContracts(hsi)
        # hsi
        # ticker = ib.reqMktData(hsi)

        data = self.ib.fills()

        df = [[i.execution.shares if i.execution.side == 'BOT' else -i.execution.shares,
               i.execution.price,
               str(i.execution.time + datetime.timedelta(hours=8))[:19],
               i.contract.localSymbol,
               i.commissionReport.commission,
               int(i.contract.multiplier),
               i.execution.orderRef] for i in data]

        df = pd.DataFrame(df, columns=['bs', 'price', 'time', 'code', 'sxf', 'hy', 'operationPeople'])
        df = df.sort_values('time')

        # 去除信息不全的单
        if self.is_clear:
            ccs = [[i.contract.localSymbol, i.position] for i in self.ib.portfolio()]
            codes = defaultdict(int)
            for i in ccs:
                codes[i[0]] += i[1]
            _s = []
            for code in set(df.code):
                k = df[df.code == code]
                ints = int(k.bs.sum() - codes[code])
                try:
                    for ind in k.index:
                        ind_bs = k.iloc[ind]['bs']
                        if (ints < 0 and ind_bs < 0 and ind_bs >= ints) or (ints > 0 and ind_bs > 0 and ind_bs <= ints):
                            ints -= ind_bs
                            _s.append(ind)
                            if ints == 0:
                                break
                except:
                    pass
            df = df.drop(_s)

        return df

    def get_gd(self):
        """ 获取当前挂单的记录 """

        if self.ib is None:
            return []

        data = self.ib.openTrades()
        gd = [[i.contract.localSymbol, str(i.log[0].time + datetime.timedelta(hours=8))[:19],
               i.order.lmtPrice, i.order.action,
               i.order.totalQuantity if i.order.action == 'BUY' else -i.order.totalQuantity,
               i.order.orderType, i.order.ocaGroup, i.order.orderRef]
              for i in data]

        gd = pd.DataFrame(gd, columns=['合约', '时间', '价格', '买卖', '数量', '订单类型', '分组名称', '订单发起人'])

        return gd

    def get_cc(self):
        """ 获取当前持仓的记录 """

        if self.ib is None:
            return []

        data = self.ib.portfolio()
        cc = [[i.contract.conId, i.contract.localSymbol, i.contract.currency,i.contract.multiplier, i.position,
               i.marketPrice,i.account, i.contract.lastTradeDateOrContractMonth]
              for i in data]

        cc = pd.DataFrame(cc, columns=['合约ID', '合约代码', '货币', '合约乘数', '数量', '价格', '账户', ' 合约过期时间'])

        return cc


    def get_lots(self,types):
        """ 获取当前持仓与挂单的占比
            types: LMT, STP LMT """

        cc = self.get_cc()
        gd = self.get_gd()
        res = defaultdict(list)
        # groupID = set()
        # for i in gd.values:
        #     if i[6] not in groupID:
        #         res[i[0]].append(i[4])
        #         groupID.add(i[6])
        [res[i[0]].append(i[4]) for i in gd.values if i[5]==types]
        [res[i[1]].append(i[4]) for i in cc.values]
        res = {i: -sum(j) for i,j in res.items()}
        return res

    def _post_order(self):
        try:
            orderHtml = self._s.post(self.url['confirmBS'], data=self.orderdata,verify=False,timeout=5)
            if self.verify_out(orderHtml):
                self._post_order()
            #print("_Post_Order  Status:",orderHtml.status_code)
            self.ptext=orderHtml.text
            forms=self.get_forms(orderHtml.text)
            forms['login_pwd']=self.account['pwd']
            #print("taken:",forms['token'])
            orderHtml = self._s.post(self.url['order'], data=forms,verify=False,timeout=5)
            print("Order Request Status:",orderHtml.status_code)
            if self.verify_error(orderHtml.text):
                self.status=2
                print("_Post_order MSG:",self.error)
        except Exception as e:
            print("System Error:",e)
            self.error="There was an error in post_order"
            self.status=2

    def order_buy(self,price,qty=1,prod_code='HSI'):
        if not prod_code:
            prod_code=self.orderdata['prod_code']
        self.orderdata['price']=str(price)
        self.orderdata['qty']=str(qty)
        self.orderdata['prod_code']=prod_code
        self.orderdata['valid_type']='0'
        self.orderdata['buy_sell']='B'
        self.orderdata['stop_type']=''
        self.orderdata['stop_price']=''
        self.orderdata['cond_text']=''
        self._post_order()   
        
    def order_sell(self,price,qty=1,prod_code='HSI'):
        print('prod code:',prod_code)
        if not prod_code:
            prod_code=self.orderdata['prod_code']
        self.orderdata['price']=str(price)
        self.orderdata['qty']=str(qty)
        self.orderdata['prod_code']=prod_code
        self.orderdata['valid_type']='0'
        self.orderdata['buy_sell']='S'
        self.orderdata['stop_type']=''
        self.orderdata['stop_price']=''
        self.orderdata['cond_text']=''
        self._post_order()  

        
    def order_stopB(self,stop_price,qty,product,add=0):
        '''限价多单止损，跌破止损价->触发空单'''
        price=stop_price-add
        prod_code=product[0:3]
        prod_month=product[3:5]
        self.orderdata['prod_code']=prod_code
        self.orderdata['contract_mth']=prod_month
        self.orderdata['price']=str(price)
        self.orderdata['qty']=str(qty)       
        self.orderdata['valid_type']='0'
        self.orderdata['buy_sell']='S'
        self.orderdata['stop_type']='L'
        self.orderdata['stop_price']=str(stop_price)
        self.orderdata['cond_text']=''
        self._post_order()
        
    def order_stopS(self,stop_price,qty,product,add=0):
        '''限价空单止损，升破止损价->触发多单'''
        price=stop_price+add
        prod_code=product[0:3]
        prod_month=product[3:5]
        self.orderdata['prod_code']=prod_code
        self.orderdata['contract_mth']=prod_month
        self.orderdata['price']=str(price)
        self.orderdata['qty']=str(qty)       
        self.orderdata['valid_type']='0'
        self.orderdata['buy_sell']='B'
        self.orderdata['stop_type']='L'
        self.orderdata['stop_price']=str(stop_price)
        self.orderdata['cond_text']=''
        self._post_order()    
    
    def get_forms(self,html):
        '''获得提交表单数据'''
        d=pq(html)
        s=d('INPUT')
        para={}
        for i in s.items():     
            if i.attr('type')=='hidden':
                para[i.attr('name')]=i.attr('value')
        return para

    #del all
    def order_delAll(self):
        """ 取消所有订单 """
        self.ib.reqGlobalCancel()

    #del order ref
    def order_del(self,orderid):
        '''del order'''
        try:
            gethtml = self.get_url(self.url['orderdetail']%orderid)
            forms=self.get_forms(gethtml)
            #print("Orderdetail Status:",gethtml.status_code)
            forms['login_pwd']=self.account['pwd']
            posthtml=self._s.post(self.url['cancelorder'],data=forms,verify=False,timeout=5)
            print("Cancel Order Status:",posthtml.status_code)
            if self.verify_error(posthtml.text):
                self.status = 2
                print("Order_del MSG:", self.error)
        except Exception as e:
            print("Order del Try_Error:",e)
        
    def get_hold(self,hh):
        '''得到最新执仓'''
        dfList=self.get_tradelist(hh)
        df2=dfList.groupby('product').trade_qty.sum()
        dictH={x[0]:0 for x in df2.iteritems()}
        dfH=pd.DataFrame(columns=['refno','product','trade_price','trade_qty','order_time','filled_qty','price','trade_time'])
        for index,row in dfList.iterrows():
            product=row['product']
            trade_qty=row.trade_qty
            if (dictH[product]>=0 and trade_qty>0) or (dictH[product]<=0 and trade_qty<0):
                dfH=dfH.append(row)
                dictH[product]+=trade_qty
                #print("go add %d %d" %(row.refno,trade_qty))
            else:
                #print("go calc %d %d" %(row.refno,trade_qty))
                dfH=self.calc_hold(dfH,row,dictH)
            #print("len dfH:",len(dfH),dictH)
        print(dictH)
        self.dictHold=dictH
        return dfH

    def calc_hold(self,dfHold,row1,dict1):
        '''for ge hold'''
        if not len(dfHold):
            return dfHold
        proc = row1['product']
        calc_qty = row1.trade_qty
        # print("func hold record:%d close:%d" %(len(dfHold),calc_qty))
        for index, row in dfHold[dfHold['product'] == proc].sort_index(ascending=False).iterrows():
            hold_qty = row.trade_qty
            if abs(hold_qty) == abs(calc_qty):
                dict1[proc] += calc_qty
                dfHold.drop(row.name, axis=0, inplace=True)
                # print("a Proc:%s Hold: %s %d，Close:%s %d" %(proc,row.refno,hold_qty,row1.refno,calc_qty))
                return dfHold
            elif abs(hold_qty) > abs(calc_qty):
                dict1[proc] += calc_qty
                dfHold.loc[row.name, 'trade_qty'] = hold_qty + calc_qty
                # print("b Proc:%s Hold: %s %d，Close:%s %d" %(proc,row.refno,hold_qty,row1.refno,calc_qty))
                return dfHold
            elif abs(hold_qty) < abs(calc_qty):
                dfHold.drop(row.name, axis=0, inplace=True)
                dict1[proc] += -hold_qty
                calc_qty += hold_qty
                # print("c Proc:%s Hold: %s %d，Close:%s %d | calc:%d,hold:%d"
                #         %(proc,row.refno,hold_qty,row1.refno,-hold_qty,calc_qty,dict1[proc]))
                if abs(calc_qty) > 0 and dict1[proc] == 0:
                    row1.trade_qty = calc_qty
                    dict1[proc] = calc_qty
                    dfHold = dfHold.append(row1)
                    # print("d go add %d %d %d" %(row1.refno,calc_qty,len(dfHold)))
                    return dfHold

    def gostop(self):
        # self.login_a()
        orderlist =self.get_orderlist()
        if self.status==999:
            print("没有正常反回数据！")
            return -1
        #tradelist=self.get_tradelist(orderlist)
        holdlist=self.get_hold(orderlist)
        for hh in self.dictHold:
            self._gostop(orderlist,holdlist,hh)

    def _gostop(self,orderlist, holdlist, proc):
        '''auto stop'''
        nostop = self.nostop
        stop_point = self.stop_point
        hh = orderlist[orderlist['product'] == proc]
        holdlist = holdlist[holdlist['product'] == proc]
        holdlist = holdlist.sort_values("trade_time", ascending=False)
        s_stop = hh.loc[(hh.status == '等待中') & (hh.cond.str.find('SL>=') > -1), 'r_qty'].sum()
        b_stop = hh.loc[(hh.status == '等待中') & (hh.cond.str.find('SL<=') > -1), 'r_qty'].sum()
        holdQty = self.dictHold[proc]
        if holdQty < 0:
            add_lots = -holdQty - s_stop - nostop
        else:
            add_lots = holdQty + b_stop - nostop
        print("%s@%d hold stop:%d@SL>=price,%d@SL<=price,Add Stop---%d@price" % (
                proc, holdQty, s_stop, b_stop, add_lots))
        if holdQty == 0 or add_lots <= 0:
            return
        cnt = 0
        for index, row in holdlist.iterrows():
            qty = row['trade_qty']
            price = row['trade_price']
            if qty < 0 and cnt <= add_lots:
                print("%s:%d@SL>=%d" % (proc, qty, price + stop_point))
                self.order_stopS(price + stop_point, qty=int(-qty), product=proc, add=0)
            elif qty > 0 and cnt <= add_lots:
                print("%s:%d@SL<=%d" % (proc, qty, price - stop_point))
                self.order_stopB(price - stop_point, qty=int(qty), product=proc, add=0)
            cnt += abs(qty)
            if cnt >= add_lots: return
                
    def get_prod(self,txt):
        '''Get the New Product List'''
        r1=re.search(self.reg['prodNameF'],txt)
        #print(r1)
        self.prodNameF=eval(r1.group(1))
        r2=re.search(self.reg['prodMonthF'],txt)
        self.prodMonthF=eval(r2.group(1))
        #print(r2)

    #del 多余的止损
    def del_stop(self):
        """ 删除多余的止损单 """
        data = self.ib.openOrders()
        [self.ib.cancelOrder(data[j]) for j, i in enumerate(data) if 'STP' in i.orderType]

    # del指定品种多余的止损单
    def _delstop(self,hh,proc):
        nostop = self.nostop
        stoplist = hh.loc[(hh['product'] == proc) & (hh.cond.str.find("SL") > -1) & (hh.status == '等待中')]
        stop_S = stoplist.loc[stoplist.r_qty > 0, 'r_qty'].sum()
        stop_B = stoplist.loc[stoplist.r_qty < 0, 'r_qty'].sum()
        if proc in self.dictHold:
            holdQty = self.dictHold[proc]
            stopQty = holdQty - nostop if holdQty >= nostop else 0
            if holdQty > 0:
                delQty = abs(stop_B) - stopQty
                self.del_stopB(delQty, stoplist)
                self.del_stopAll('S', stoplist)
            elif holdQty < 0:
                delQty = stop_S - stopQty
                self.del_stopS(delQty, stoplist)
                self.del_stopAll('B', stoplist)
            else:
                self.del_stopAll('B', stoplist)
                self.del_stopAll('S', stoplist)
        else:
            self.del_stopAll('B', stoplist)
            self.del_stopAll('S', stoplist)

    #del stop order
    def del_stopB(self,delqty,hh):
        cont = "SL<="
        delpd = hh.loc[(hh.status == '等待中') & (hh.cond.str.find(cont) > -1)].copy()
        if delqty <= 0 or not len(delpd): return
        delpd = delpd.sort_index(ascending=True)
        for index, rows in delpd.iterrows():
            if rows.sqty <= delqty:
                print("del order %s refno:%d %d" %(rows['product'],rows.refno, rows.sqty))
                self.order_del(rows.refno)
            elif rows.sqty > delqty:
                self.order_del(rows.refno)
                print("del order refno:", rows.refno, delqty)
                stop_price = int(rows.cond[4:].replace(',', ''))
                qty = rows.sqty - delqty
                product = rows['product']
                add = stop_price - rows.price
                self.order_stopB(stop_price, qty, product, add=add)
                print('add  stopB:stop_price=%d,qty=%d,product=%s,add=%d' % (stop_price, qty, product, add))
            delqty = delqty - rows.sqty
            if delqty <= 0: break

    #del stop order
    def del_stopS(self,delqty,hh):
        cont = "SL>="
        delpd = hh.loc[(hh.status == '等待中') & (hh.cond.str.find(cont) > -1)].copy()
        if delqty <= 0 or not len(delpd): return
        delpd = delpd.sort_index(ascending=True)
        for index, rows in delpd.iterrows():
            if rows.bqty <= delqty:
                print("del order refno:", rows.refno, rows.bqty)
                self.order_del(rows.refno)
            elif rows.bqty> delqty:
                self.order_del(rows.refno)
                print("del order refno:", rows.refno, delqty)
                stop_price = int(rows.cond[4:].replace(',', ''))
                qty = rows.bqty - delqty
                product = rows['product']
                add =rows.price-stop_price
                self.order_stopS(stop_price, qty, product, add=add)
                print('add  stopB:stop_price=%d,qty=%d,product=%s,add=%d' % (stop_price, qty, product, add))
            delqty = delqty - rows.bqty
            if delqty <= 0: break

    # del stop all
    def del_stopAll(self,buy_sell):
        data = self.ib.openOrders()
        if buy_sell=='B':
            cont = 'SELL'
        else:
            cont = 'BUY'
        [self.ib.cancelOrder(data[j]) for j, i in enumerate(data) if i.action == cont and 'STP' in i.orderType]
        # delpd = hh.loc[(hh.status == '等待中') & (hh.cond.str.find(cont) > -1)].copy()
        # if  not len(delpd): return
        # delpd = delpd.sort_index(ascending=True)
        # for index, rows in delpd.iterrows():
        #     print("del order refno:", rows.refno, rows.bqty)
        #     self.order_del(rows.refno)


def save_ib_trade(file, dbhost=None, dbport=None, dbuser=None, dbpwd=None):
    """ 读取IB导出的TXT文件并保存到数据库"""
    if not (dbhost and dbport and dbuser and dbpwd):
        conf = configparser.ConfigParser()
        conf.read('util.log')
        dbhost = conf['MongoDB']['host']
        dbport = int(conf['MongoDB']['port'])
        dbuser = conf['MongoDB']['user']
        dbpwd = conf['MongoDB']['pswd']
    client = pm.MongoClient(dbhost, dbport)
    client.admin.authenticate(dbuser, dbpwd)
    db = client.IB
    col = db.get_collection('Trade')
    trade_data = pd.read_csv(file)
    is_for = False
    for _, v in trade_data.iterrows():
        is_for = True
        t = parser.parse(f"{v['Date']} {v['Time']}")
        _v = { 'time': t,
                 'contract': {'secType': v['Security Type'],
                  'conId': None,
                  'symbol': v['Underlying'],
                  'lastTradeDateOrContractMonth': v['Last Trading Day'],
                  'strike': v['Strike'] if not np.isnan(v['Strike'] ) else 0.0,
                  'right': '',
                  'multiplier': '50',
                  'exchange': v['Exch.'],
                  'primaryExchange': '',
                  'currency': 'HKD',
                  'localSymbol': v['Symbol'],
                  'tradingClass': v['Trading Class'],
                  'includeExpired': False,
                  'secIdType': '',
                  'secId': '',
                  'comboLegsDescrip': '',
                  'comboLegs': None,
                  'deltaNeutralContract': None},
                 'execution': {'execId': v['ID'],
                  'time': t,
                  'acctNumber': v['Account'],
                  'exchange': v['Exch.'],
                  'side': v['Action'],
                  'shares': v['Quantity'],
                  'price': v['Price'],
                  'permId': "",
                  'clientId': 0,
                  'orderId': 0,
                  'liquidation': 0,
                  'cumQty': v['Quantity'],
                  'avgPrice': v['Price'],
                  'orderRef': v['Order Ref.'],
                  'evRule': '',
                  'evMultiplier': 0.0,
                  'modelCode': '',
                  'lastLiquidity': 1},
                 'commissionReport': {'execId': v['ID'],
                  'commission': v['Commission'],
                  'currency': v['Currency'],
                  'yield_': 0.0,
                  'yieldRedemptionDate': 0}}

        if not np.isnan(v['Realized P&L']):
            _v['realizedPNL'] = v['Realized P&L']

        try:
            col.insert(_v)
        except pm.errors.DuplicateKeyError:
            print(f"{_v['execution']['execId']}已存在")
        else:
            print(f"{_v['execution']['execId']}成功入库")
    if not is_for:
        raise Exception('for循环未执行！')

print("import OK")
