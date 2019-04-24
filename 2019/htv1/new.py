from htisec import Hsi, save_ib_trade
from jy import HS2
from win_ui import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QTimer
import time
import datetime
import json
import os
import sys
import math
import uuid
import asyncio
import calendar
import pandas as pd

from threading import Thread
from ib_insync import LimitOrder, Future, IB, util, StopLimitOrder


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.HS = HS2()
        self.setupUi(self)
        #self.timer=QTimer(self)
        #self.b_autostop.setEnabled(True)
        #self.b_pause.setEnabled(False)
        self.setWindowTitle("盈透证券交易助手V2.1")
        self.l_user.setText("")
        self.l_pwd.setText("")

        #self.timer.timeout.connect(self.t_autodo)
        # Login
        self.b_login.clicked.connect(self.c_login)
        #self.b_autostop.clicked.connect(self.c_autostop)
        #self.b_pause.clicked.connect(self.c_pause)
        self.b_checkstop.clicked.connect(self.c_checkstop)
        self.b_buy.clicked.connect(self.c_buy)
        self.b_sell.clicked.connect(self.c_sell)
        self.b_stopbuy.clicked.connect(self.c_stopbuy)
        self.b_stopsell.clicked.connect(self.c_stopsell)
        self.b_save_file.clicked.connect(self.c_save_file)
        self.b_orderlist.clicked.connect(self.c_orderlist)
        self.b_test.clicked.connect(self.c_test)
        self.b_test1.clicked.connect(self.c_test1)
        self.b_gostop.clicked.connect(self.c_gostop)
        self.b_delStop.clicked.connect(self.c_delStop)
        self.b_delAll.clicked.connect(self.c_delAll)
        self.b_delStopB.clicked.connect(self.c_delStopB)
        self.b_delStopS.clicked.connect(self.c_delStopS)
        self.b_info.clicked.connect(self.c_info)
        self.rStop1.clicked.connect(self.chg_radio)
        self.rStop2.clicked.connect(self.chg_radio)
        self.rStop3.clicked.connect(self.chg_radio)
        self.rClose1.clicked.connect(self.chg_close)
        self.rClose2.clicked.connect(self.chg_close)
        self.rClose3.clicked.connect(self.chg_close)
        # commbox box_product
        self.box_product.currentTextChanged.connect(self.prod_change)
        self.box_stop_type.currentTextChanged.connect(self.stop_change)
        self.box_diff.valueChanged.connect(self.chg_radio)
        self.box_lot1.valueChanged.connect(self.chg_lot1_a)
        self.box_nostop.valueChanged.connect(self.chg_lot1_b)
        self.box_add.valueChanged.connect(self.chg_radio)
        self.box_c1.valueChanged.connect(self.boxc1_chg)
        self.box_c2.valueChanged.connect(self.boxc2_chg)
        self.box_c3.valueChanged.connect(self.chg_lot2_b)
        self.box_lot2.valueChanged.connect(self.chg_lot2_a)
        self.b_close1.clicked.connect(self.cb_close1)

        self.load_info()
        self.user = None
        self.pwd_id = None

        self.zszyAll = {'zs': [], 'zy': []}  # 止损止盈组列表

        self.time = 0

    #save person info
    def c_info(self):
        user = self.l_user.text()
        pwd = self.l_pwd.text()
        add = self.box_add.value()
        diff = self.box_diff.value()
        nostop = self.box_nostop.value()
        noclose=self.box_c3.value()
        #time = self.box_time.value()
        add2 = self.box_add2.value()
        qty = self.box_qty.value()
        info = {
            "user": user,
            "pwd": pwd,
            "add": add,
            "diff": diff,
            "nostop": nostop,
            "add2": add2,
            "qty": qty,
            "noclose":noclose,
            "automaticallyRefresh": self.automaticallyRefresh,
        }
        print(info)
        jsObj = json.dumps(info)
        fileObject = open('info.dll', 'w')
        fileObject.write(jsObj)

    def closeEvent(self, ev):
        """ 关闭程序 """
        asyncio.get_event_loop().stop()

    def c_pause(self):
        print("auto exec Pause:")
        self.timer.stop()
        self.b_autostop.setEnabled(True)
        self.b_pause.setEnabled(False)

    def t_autodo(self):
        self.stopNO+=1
        print("autodo_Time%s,No:%d" %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),self.stopNO))
        self.c_checkstop()
        self.c_delStop()
        if web_trade.status==999:
            web_trade.login_a()

    #to auto check stop order
    def c_autostop(self):
        if not web_trade.status:
            w.statusBar().showMessage('没有登陆!')
            return
        print("atuo exec Bgin:")
        #diff=self.box_time.value()*1000
        # self.timer.start(diff)
        self.b_autostop.setEnabled(False)
        self.b_pause.setEnabled(True)
        self.stopNO=0

    def c_orderlist_thread(self):
        """" 线程刷新 """
        t = Thread(target=self.c_orderNews)
        t.start()


    #delete stop B all
    def c_delStopB(self):
        """ 删除多单的止损(空) """
        if self.check_login(): return
        web_trade.del_stopAll('B')
        self.zszyAll['zs'] = []
        self.c_orderlist()
        self.c_orderlist_thread()

    #delete stop B all
    def c_delStopS(self):
        """  删除空单的止损(多) """
        if self.check_login(): return
        web_trade.del_stopAll('S')
        self.zszyAll['zs'] = []
        self.c_orderlist()
        self.c_orderlist_thread()

    # delete all
    def c_delAll(self):
        """ 删除未成交的单 """
        if self.check_login(): return
        web_trade.order_delAll()
        self.zszyAll = {'zs': [], 'zy': []}
        self.c_orderlist()
        self.c_orderlist_thread()

    # delete stop
    def c_delStop(self):
        """ 删除多余的止损单 """
        if self.check_login(): return
        web_trade.nostop=self.box_nostop.value()
        web_trade.del_stop()
        self.zszyAll['zs'] = []
        self.c_orderlist()
        self.c_orderlist_thread()

    #check not login
    def check_login(self):
        if not web_trade.status:
            w.statusBar().showMessage('没有登陆!')
            return True
        else:
            return False

    #Test button
    def c_test(self):
        if self.check_login(): return
        self.show_stop()

    def show_stop(self):
        if not hasattr(self,'set1'):
            print('Not Set1')
            return None, None
        set1=self.set1
        hold=set1['持仓']
        h_cost=math.ceil(set1['原始成本'])
        h_costA = set1['净会话成本']
        h_costB = set1['净持仓成本']
        #print("参考开仓成本  %d@%f" %(hold,h_cost))
        self.txt1.setText("%d@%f" %(hold,h_cost))
        self.txt2.setText ( "%d@%f" % (hold, h_costA))
        self.txt3.setText ( "%d@%f" % (hold, h_costB))
        self.txt_c1.setText("%d@%f" %(hold,h_cost))
        self.txt_c2.setText("%d@%f" % (hold, h_costA))
        self.txt_c3.setText("%d@%f" % (hold, h_costB))
        self.boxc1_chg()
        self.chg_lot1_b()
        self.chg_lot2_b()
        #self.calc_close()
        #self.calc_stop()
    #test1 button
    def c_test1(self):
        if self.check_login(): return
        if web_trade.is_clear == False:
            web_trade.is_clear = True
            self.b_test1.setText('不去除')
        else:
            web_trade.is_clear = False
            self.b_test1.setText('去除')

        # get orderlist
        # hh = web_trade.get_orderlist()
        # if web_trade.status == 999:
        #     print("get_orderlist没有返回数据[c_orderlist]")
        #     return -1
        # tradelist = web_trade.get_tradelist(hh)
        tradelist = web_trade.get_tradelist()
        gd = web_trade.get_gd()
        cc = web_trade.get_cc()

        if tradelist is not None:
            self.get_comm(tradelist, gd, cc)


    #取得会话记录
    def get_comm(self,tradelist,gd,cc):
        # df1 = list1[['trade_qty', 'trade_price', 'trade_time','product']]
        # df2 = df1.fillna(0)
        # df2.columns = ['bs', 'price', 'time','product']
        h = self.HS

        try:
            df2 = h.ray(tradelist)
            rows = df2.copy()
            self.set1 = df2.iloc[-1]
            self.show_table(rows, self.table_comm)
            self.show_table(tradelist, self.table_his)
        except Exception as exc:
            print('没有交易记录...')
        # df2 = h.ray(df2)


        # rows2 = rows[rows[rows['持仓']==0].index[-1]+1:] if len(rows[rows['持仓']==0])>0 else rows
        # rows3 = []
        # ind = None
        # for i in rows2.values:
        #     if ind is None:
        #         ind = True if i[2]>0 else False
        #     rows3.append(i)
        #     if len(rows3)>1 and (ind and i[2]<0 or not ind and i[2]>0):
        #         rows3.pop()
        #         rows3.pop()
        # rows3 = pd.DataFrame(rows3,columns=rows.columns)
        self.show_table(cc, self.table_hold)
        self.show_table(gd, self.table_wait)

    #load info
    def load_info(self):
        try:
            if os.path.exists("info.dll"):
                ff = open("info.dll", encoding='utf-8')
                txt = ff.read()
                info=eval(txt)
                self.l_user.setText(info["user"])
                self.l_pwd.setText(info["pwd"])
                self.box_add.setValue(info["add"])
                self.box_diff.setValue(info["diff"])
                self.box_nostop.setValue(info["nostop"])
                self.box_c3.setValue(info["noclose"])
                #self.box_time.setValue(info["time"])
                self.box_qty.setValue(info["qty"])
                self.box_add2.setValue(info["add2"])
                self.automaticallyRefresh = info["automaticallyRefresh"]
        except Exception as e:
            print("Error:load_info",e)

    def show_table(self,rows,table):
        ll = [i for i in rows.columns]
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setColumnCount(len(ll))
        table.setRowCount(len(rows))
        table.setHorizontalHeaderLabels(ll)
        for x in range(len(ll)):
            headItem = table.horizontalHeaderItem(x)  # 获得水平方向表头的Item对象
            #headItem.setFont("新宋体")  # 设置字体
            headItem.setBackground(QColor(0x8f, 0x8f, 0x8f))  # 设置单元格背景颜色
        row_index = 0
        for index, row in rows.iterrows():
            i = 0
            for vv in row:
                self.newItem = QtWidgets.QTableWidgetItem(str(vv))
                if row_index % 2:
                    self.newItem.setBackground(QColor(0xcf,0xcf,0xcf))
                table.setItem(row_index, i, self.newItem)
                i = i + 1
            row_index += 1
        table.resizeColumnsToContents()
        table.resizeColumnsToContents()

    def c_orderNews(self):
        """ 订单变更 """
        this_time = time.time()
        if this_time-self.time <= 1:
            time.sleep(2)
        elif this_time - self.time <= 2:
            time.sleep(1)
        self.time = this_time

        tradelist = web_trade.get_tradelist()
        gd = web_trade.get_gd()
        cc = web_trade.get_cc()
        if tradelist is not None:
            self.get_comm(tradelist, gd, cc)


    def c_orderlist_auto(self, trade):
        print('订单变更...')
        try:
            print(str(trade.log[0].time+datetime.timedelta(hours=8))[:22], trade.orderStatus)
        except:
            pass

        self.c_orderlist_thread()


    #get orderlist
    def c_orderlist(self):
        print('刷新...')
        if self.check_login():
            return
        web_trade.ib.waitOnUpdate(timeout=0.1)
        # self.HS.ib = None
        # self.HS = HS2()
        tradelist = web_trade.get_tradelist()
        gd = web_trade.get_gd()
        cc = web_trade.get_cc()

        if tradelist is not None:
            self.get_comm(tradelist, gd, cc)
        # if self.check_login():return
        # #get orderlist
        # hh = web_trade.get_orderlist()
        # if web_trade.status==999:
        #     print("get_orderlist没有返回数据[c_orderlist]")
        #     return -1
        # tradelist=web_trade.get_tradelist(hh)
        # hold = web_trade.get_hold(hh)
        # cols = ['refno', 'product', 'trade_price','trade_qty','trade_time','price', 'filled_qty','r_qty', 'initiator', 'order_time', 'status']
        # rows = tradelist[ cols].copy()
        # self.show_table(rows, self.table_his)
        # cols = ['refno', 'product', 'price', 'filled_qty','r_qty','cond', 'initiator', 'order_time', 'status']
        # rows = hh.loc[hh.status.isin(['等待中','工作中']) , cols].copy()
        # self.show_table(rows, self.table_wait)
        # cols = ['refno', 'product','trade_price','trade_qty','trade_time', 'price', 'filled_qty','r_qty', 'initiator', 'order_time', 'status']
        # rows=hold[cols].copy()
        # self.show_table(rows, self.table_hold)
        # self.get_comm(tradelist)
        # self.show_stop()
        # w.statusBar().showMessage("交易刷新成功!")

    #止损
    def c_gostop(self):
        if self.check_login(): return
        getLots=self.box_lot1.value()
        if getLots==0:
            return
        Lots, StopPrice =self.calc_stop()

        if Lots is None or StopPrice is None:
            return
        addon=self.box_add.value()
        prod = self.set1['合约']

        web_trade.ib.waitOnUpdate(0.1)
        able_lots = web_trade.get_lots('STP LMT')

        if prod not in able_lots or able_lots[prod] == 0:
            return

        if abs(Lots) > abs(able_lots[prod]):
            Lots = able_lots[prod]

        lotsList=self.getList(abs(int(Lots)))

        # print(getLots,Lots,StopPrice,addon,prod,lotsList)

        hsi = Future(localSymbol=prod)
        if web_trade.ib.qualifyContracts(hsi):
            if Lots>0:
                for i in lotsList:
                    # web_trade.order_stopS(StopPrice,i,prod,addon)
                    zs, thereAre = self.zszyGroup('zs')
                    order = StopLimitOrder('BUY', i, StopPrice+addon, StopPrice,
                                           ocaGroup=zs, ocaType=2, orderRef=f"PY_{self.pwd_id[-1]}")
                    web_trade.ib.placeOrder(hsi,order)


                    print("%d@%d-%s"%(i,StopPrice,prod))
            else:
                for i in lotsList:
                    # web_trade.order_stopB(StopPrice,i, prod,addon)
                    zs, thereAre = self.zszyGroup('zs')
                    order = StopLimitOrder('SELL', i, StopPrice - addon, StopPrice,
                                           ocaGroup=zs, ocaType=2, orderRef=f"PY_{self.pwd_id[-1]}")
                    web_trade.ib.placeOrder(hsi, order)

                    print("%d@%d-%s" % (-i, StopPrice, prod))
        self.box_lot1.setValue(0)
        self.c_orderlist()


    #触发多单
    def c_stopbuy(self):
        self.c_stop("B")
        self.c_orderlist()

    #触发空单
    def c_stopsell(self):
        print('止损多单...')
        self.c_stop("S")
        self.c_orderlist()

    #止损触发
    def c_stop(self,buy_sell):
        if self.check_login(): return
        prod = self.box_product.currentText()[0:3]
        prodM = self.box_month.currentText()[0:6]
        qty=self.box_qty.value()
        stop_price=self.box_stop_price.value()
        stop_type = self.box_stop_type.currentText()[0:1]
        addon=self.box_add2.value()
        # print(prod, prodM, qty, stop_price, stop_type, addon)

        hsi = Future(prod, prodM)
        if web_trade.ib.qualifyContracts(hsi):
            if buy_sell == 'B':
                order = StopLimitOrder('BUY', qty, stop_price+addon, stop_price,
                                       outsideRth=self.c_t1.isChecked(), orderRef=f"PY_{self.pwd_id[-1]}")
            else:
                order = StopLimitOrder('SELL', qty, stop_price-addon, stop_price,
                                       outsideRth=self.c_t1.isChecked(), orderRef=f"PY_{self.pwd_id[-1]}")
            web_trade.ib.placeOrder(hsi, order)

            if web_trade.status == 2:
                w.statusBar().showMessage(web_trade.error)



    def c_order(self, buy_sell):
        '''click buy button'''
        if self.check_login(): return
        prod = self.box_product.currentText()[0:3]
        prodM = self.box_month.currentText()[0:6]
        price = self.box_price.value()
        qty = self.box_qty.value()

        hsi = Future(prod, prodM)
        if web_trade.ib.qualifyContracts(hsi):
            if buy_sell == 'B':
                order = LimitOrder('BUY', qty, price,
                                   outsideRth=self.c_t1.isChecked(), orderRef=f"PY_{self.pwd_id[-1]}")
            else:
                order = LimitOrder('SELL', qty, price,
                                   outsideRth=self.c_t1.isChecked(), orderRef=f"PY_{self.pwd_id[-1]}")
            web_trade.ib.placeOrder(hsi, order)
            print("%s%s %d@%d" % (prod, prodM, qty if buy_sell == 'B' else -qty, price))
            if web_trade.status == 2:
                w.statusBar().showMessage(web_trade.error)


    def c_sell(self):
        '''Click Sell Button'''
        print('sell.....')
        self.c_order('S')
        self.c_orderlist()

    def c_buy(self):
        '''Click Buy Button'''
        print('buy......')
        self.c_order('B')
        self.c_orderlist()

    # login
    def c_login(self):
        """ 登录 """
        user = self.l_user.text()
        pwd_id = (self.l_pwd.text()).split('/')
        pwd = int(pwd_id[0])
        clientId = int(pwd_id[1])

        if not self.user or (user != self.user or self.pwd_id != pwd_id):
            if self.user:
                web_trade.ib.disconnect()
                web_trade.ib = None

            ib = web_trade.login_1(user, pwd, clientId)

            if ib is None:
                w.statusBar().showMessage("登陆不成功!")
                return
            w.statusBar().showMessage("登陆成功!")

            # ib.openOrderEvent += self.c_orderlist_auto
            ib.orderStatusEvent += self.c_orderlist_auto

            self.user = user
            self.pwd_id = pwd_id
            web_trade.error=1
            web_trade.status=1
        #get trade product
        # txt = web_trade.get_orderpage()
        # web_trade.get_prod(txt)
        # self.box_product.clear()
        # self.box_month.clear()
        # for prod in web_trade.prodNameF:
        #     self.box_product.addItem(web_trade.prodNameF[prod])
        # set stop_type
        # stop_type = ["L-限价止损", "U-升市触发", "D-跌市触发"]
        # for ll in stop_type:
        #     self.box_stop_type.addItem(ll)
        #show orderlist

        wb = {'HSI': 'HSI-恒生指数', 'HHI': 'HHI-H股指数', 'MHI': 'MHI-小型恒生指数', 'MCH': 'MCH-小型H股指数',
              'DHS': 'DHS-恒指股息', 'DHH': 'DHH-恒生国企股息', 'VHS': 'VHS-恒指波幅指数'}

        for prod in wb: #web_trade.prodNameF:
            self.box_product.addItem(wb[prod])
        self.c_orderlist()


    #check stop order
    def c_checkstop(self):
        # if self.check_login(): return
        # web_trade.stop_point = self.box_diff.value()
        # web_trade.nostop = self.box_nostop.value()
        # web_trade.gostop()
        # self.c_orderlist()
        # if web_trade.status == 2:
        #     w.statusBar().showMessage(web_trade.error)
        print('逐单止损...')


    def stop_change(self):
        curtext = self.box_stop_type.currentText()[0:1]
        if curtext == 'L':
            self.gr_stop.setTitle("限价触发: >=[触发价] 触发多单  ｜ <=[触发价] 触发空单")
        elif curtext == 'U':
            self.gr_stop.setTitle("升市触发：>=[触发价] 触发多单  ｜ >=[触发价] 触发空单")
        else:
            self.gr_stop.setTitle("跌市触发：<=[触发价] 触发多单  ｜ <=[触发价] 触发空单")

    # commbox prod_change
    def prod_change(self):
        # try:
        #     self.box_month.clear()
        #     self.box_month.setCurrentText("a")
        #     prod = self.box_product.currentText()[0:3]
        #     # w.statusBar().showMessage(self.box_product.currentText())
        #     month = web_trade.prodMonthF[prod]
        #     #print(month)
        #     for mm in month:
        #         self.box_month.addItem("%s-%s" % (mm, month[mm]))
        # except Exception as e:
        #     print("prod_change Try_Error:",e)

        this_dt = datetime.datetime.now()
        first_day = datetime.date(this_dt.year, this_dt.month, 1)
        days_num = calendar.monthrange(first_day.year, first_day.month)[1]  # 获取一个月有多少天
        next_month = first_day + datetime.timedelta(days=days_num)  # 获取下月

        this_month = str(this_dt).replace('-','')[:6]
        next_month = str(next_month).replace('-','')[:6]
        month = {this_month, next_month}  # {'F8': '2018/01', 'G8': '2018/02', 'H8': '2018/03', 'M8': '2018/06'}
        for mm in month:
            self.box_month.addItem(mm)

    #radio button rStop1
    def c_rStop1(self):
        self.gr_stop.setTitle("止损选项--radio 1")

    #change stop lots
    def chg_lot1_a(self):
        if not hasattr(self,'set1'):
            print('Not Set1')
            return
        hold=abs(self.set1['持仓'])
        if hold==0:
            return

        lots = self.box_lot1.value()
        noClose=self.box_nostop.value()
        if lots>hold:
            self.box_lot1.setValue(hold)
            self.box_nostop.setValue(0)
        else:
            self.box_nostop.setValue(hold-lots)

        self.calc_stop()

    # change stop lots
    def chg_lot1_b(self):
        if not hasattr(self, 'set1'):
            print('Not Set1')
            return
        hold = abs(self.set1['持仓'])
        if hold == 0:
            return

        lots = self.box_lot1.value()
        noStop = self.box_nostop.value()
        if noStop > hold:
            self.box_nostop.setValue(hold)
            self.box_lot1.setValue(0)
        else:
            self.box_lot1.setValue(hold-noStop)

        self.calc_stop()

    #change close lots
    def chg_lot2_a(self):
        if not hasattr(self,'set1'):
            print('Not Set1')
            return
        hold=abs(self.set1['持仓'])
        if hold==0:
            return

        lots = self.box_lot2.value()
        noClose=self.box_c3.value()
        if lots>hold:
            self.box_lot2.setValue(hold)
            self.box_c3.setValue(0)
        else:
            self.box_c3.setValue(hold-lots)

        self.calc_close()

    # change close lots
    def chg_lot2_b(self):
        if not hasattr(self, 'set1'):
            print('Not Set1')
            return
        hold = abs(self.set1['持仓'])
        if hold == 0:
            return

        lots = self.box_lot2.value()
        noClose = self.box_c3.value()
        if noClose > hold:
            self.box_c3.setValue(hold)
            self.box_lot2.setValue(0)
        else:
            self.box_lot2.setValue(hold-noClose)

        self.calc_close()

    #box_c1 change
    def boxc1_chg(self):
        if not hasattr(self,'set1'):
            print('Not Set1')
            return

        hold=self.set1['持仓']
        if hold==0:
            return

        if self.rClose1.isChecked():
            cost=self.set1['原始成本']
        elif self.rClose2.isChecked():
            cost = self.set1['净会话成本']
        elif self.rClose3.isChecked():
            cost = self.set1['净持仓成本']

        prod=self.set1['合约']
        if prod[0:3]=='HSI':
            point=50
        elif prod[0:3]=='MHI':
            point=10

        win = self.box_c1.value()
        profit = abs(hold) * point * win
        self.box_c2.setValue(profit)
        self.calc_close()

    #box_c2 change
    def boxc2_chg(self):
        if not hasattr(self,'set1'):
            print('Not Set1')
            return

        hold=self.set1['持仓']
        if hold==0:
            return

        if self.rClose1.isChecked():
            cost=self.set1['原始成本']
        elif self.rClose2.isChecked():
            cost = self.set1['净会话成本']
        elif self.rClose3.isChecked():
            cost = self.set1['净持仓成本']

        prod=self.set1['合约']
        if prod[0:3]=='HSI':
            point=50
        elif prod[0:3]=='MHI':
            point=10

        profit = self.box_c2.value()
        win=math.ceil(profit/point/abs(hold))
        self.box_c1.setValue(win)
        self.calc_close()

    #close radio change
    def chg_close(self):
        self.calc_close()


    #calc close Price
    def calc_close(self):
        if not hasattr(self,'set1'):
            print('Not Set1')
            return None, None

        hold=self.set1['持仓']
        if hold==0:
            return None, None

        prod=self.set1['合约']
        if prod[0:3]=='HSI':
            point=50
            charg=33.54
        elif prod[0:3]=='MHI':
            point=10
            charg=13.6

        win = self.box_c1.value()
        #profit=self.box_c2.value()
        getLots=self.box_lot2.value()

        if self.rClose1.isChecked():
            cost=math.ceil(self.set1['原始成本'])
            preProfit=self.set1['净利润']
            Charges = self.set1['手续费']
            Charg1=charg*abs(hold)
            win=math.ceil(win+charg*2/point)
        elif self.rClose2.isChecked():
            cost = self.set1['净会话成本']
            comHold=self.set1['会话盈利']/self.set1['会话平均盈利'] if self.set1['会话平均盈利']!=0 else 0
            closeHold = self.set1['已平仓']
            Charges = (closeHold-comHold)*charg*2
            preProfit = self.set1['利润']-self.set1['会话盈利']*point-Charges
            Charg1=comHold*charg*2+abs(hold)*charg*2
            win=math.ceil(Charg1/point/abs(hold)+win)
        elif self.rClose3.isChecked():
            cost = self.set1['净持仓成本']
            Charges = self.set1['手续费']
            preProfit=-Charges
            Charg1 = charg * abs(hold)
            closeHold=self.set1['已平仓']
            win=math.ceil((Charges+Charg1)/point/abs(hold)+win)

        #hold buy
        if hold>0:
            ClosePrice=cost+win
            lots=-getLots
        else:
            ClosePrice = cost -win
            lots=getLots


        curProfit=preProfit+win*abs(hold)*point-Charg1
        curCharges=Charges+abs(hold)*charg

        inf="止盈单:%d@%d|Pre:%.2f + %.2f|Cur:%.2f + %.2f" \
            %(lots,ClosePrice,preProfit,Charges,curProfit,curCharges)
        self.grClose.setTitle(inf)
        return lots,ClosePrice


    def zszyGroup(self, types):
        """ 止损止盈组
            types: zs,zy"""
        if types == 'zs':
            z1 = 'zs'
            z2 = 'zy'
        elif types == 'zy':
            z1 = 'zy'
            z2 = 'zs'
        else:
            raise Exception('error: zszyGroup types!')
        thereAre = False
        if len(self.zszyAll[z1]) < len(self.zszyAll[z2]):
            zy = None
            for zy in self.zszyAll[z2]:
                if zy not in self.zszyAll[z1]:
                    thereAre = True
                    break
            if zy is None:
                zy = str(uuid.uuid4())[-12:]
                self.zszyAll[z1].append(zy)
            else:
                self.zszyAll[z2].remove(zy)
        else:
            zy = str(uuid.uuid4())[-12:]
            self.zszyAll[z1].append(zy)

        return zy, thereAre


    #click 止盈
    def cb_close1(self):
        if self.check_login(): return

        getLots=self.box_lot2.value()
        if getLots==0:
            return

        Lots, Price = self.calc_close()
        if Lots is None or Price is None:
            return

        prod = self.set1['合约']

        web_trade.ib.waitOnUpdate(0.1)
        able_lots = web_trade.get_lots('LMT')

        if prod not in able_lots or able_lots[prod]==0:
            return
        if abs(Lots) > abs(able_lots[prod]):
            Lots = able_lots[prod]
        # prod_code=prod[0:3]
        # prod_month=prod[3:5]
        # web_trade.orderdata['prod_code'] = prod_code
        # web_trade.orderdata['contract_mth'] = prod_month
        lotsList = self.getList(abs(int(Lots)))
        # print(getLots,prod,Lots,Price,lotsList,self.c_close1.isChecked())

        hsi = Future(localSymbol=prod)
        if web_trade.ib.qualifyContracts(hsi):
            if Lots >0:
                for x in lotsList:
                    # web_trade.order_buy(Price, x, prod_code=prod_code)
                    zy, thereAre = self.zszyGroup('zy')
                    order = LimitOrder('BUY', x, Price, ocaGroup=zy, ocaType=2,
                                       outsideRth=self.c_close1.isChecked(), orderRef=f"PY_{self.pwd_id[-1]}")
                    web_trade.ib.placeOrder(hsi, order)

                    print("%s %d@%d" % (prod,  x, Price))
            else:
                for x in lotsList:
                    # web_trade.order_sell(Price, x, prod_code=prod_code)
                    zy, thereAre = self.zszyGroup('zy')
                    order = LimitOrder('SELL', x, Price, ocaGroup=zy, ocaType=2,
                                       outsideRth=self.c_close1.isChecked(), orderRef=f"PY_{self.pwd_id[-1]}")
                    web_trade.ib.placeOrder(hsi, order)

                    print("%s -%d@%d" % (prod, x, Price))
        self.box_lot2.setValue(0)
        self.c_orderlist()

    #chg radio
    def chg_radio(self):
        self.calc_stop()

    def calc_stop(self):
        if not hasattr(self,'set1'):
            print('Not Set1')
            return None, None
        hold=self.set1['持仓']
        if hold==0:
            return None, None

        prod=self.set1['合约']
        if prod[0:3]=='HSI':
            point=50
            charg=33.54
        elif prod[0:3]=='MHI':
            point=10
            charg=13.6

        stop_point = self.box_diff.value()
        nostop = self.box_nostop.value()
        addon=self.box_add.value()
        getLots = self.box_lot1.value()

        if self.rStop1.isChecked():
            cost=math.ceil(self.set1['原始成本'])
            preProfit=self.set1['净利润']
            Charges = self.set1['手续费']
            Charg1=charg*abs(hold)
        elif self.rStop2.isChecked():
            cost = self.set1['净会话成本']
            comHold=self.set1['会话盈利']/self.set1['会话平均盈利']
            closeHold = self.set1['已平仓']
            Charges = (closeHold-comHold)*charg*2
            preProfit = self.set1['利润']-self.set1['会话盈利']*point-Charges
            Charg1=comHold*charg*2+abs(hold)*charg*2
        elif self.rStop3.isChecked():
            cost = self.set1['净持仓成本']
            Charges = self.set1['手续费']
            preProfit=-Charges
            closeHold=self.set1['已平仓']
            Charg1=charg*abs(hold)

        if hold>0:
            lots=-getLots
            StopPrice=cost-stop_point
            sign='SL<'
        elif hold<0:
            lots=getLots
            StopPrice=cost+stop_point
            sign='SL>'
        else:
            lots=0
            StopPrice=0
            sign='L>'

        curProfit=preProfit-point*abs(hold)*(stop_point+addon)-Charg1
        curCharges=Charges+Charg1

        inf="止损单:%d@%s%f+%d|Pre:%.2f + %.2f|Cur:%.2f + %.2f" \
            %(lots,sign,StopPrice,addon,preProfit,Charges,curProfit,curCharges)
        #inf="上损:%d@%s%f+%d" %(lots,sign,StopPrice,addon)
        self.grStop.setTitle(inf)
        return lots,StopPrice

    def getList(self,lots):
        # if lots == 1:
        #     ll = [1]
        # elif lots < 7:
        #     a = lots % 2
        #     b = int(lots / 2)
        #     ll = [b + a, b]
        # elif lots < 13:
        #     a = lots % 3
        #     b = int(lots / 3)
        #     ll = [b + a, b, b]
        # else:
        #     a = lots % 4
        #     b = int(lots / 4)
        #     ll = [b + a, b, b, b]
        ll = [1 for i in range(lots)]
        return ll

    def c_save_file(self):
        """ 保存交易记录 """
        fileName, filetype = QFileDialog.getOpenFileName(self, "选择文件", "")
        if fileName:
            try:
                save_ib_trade(fileName)
                w.statusBar().showMessage("已经成功保存！")
            except:
                print('错误：文件格式不匹配！')
                w.statusBar().showMessage("错误：文件格式不匹配！")


if __name__ == "__main__":
    util.patchAsyncio()
    util.useQt()
    web_trade = Hsi()
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    style='''
    QWidget
    {
    color:#8B6914;
       background-color:qlineargradient(spread:pad, x1: 0, y1: 0, x2: 1, y2: 1,
                                      stop: 0 #EFEFFD, stop: 1 #D6C3A0 );
    }
    QStatusBar {
    background: #E5E5E5;
    color:red;
    border: 1px solid #5465E7;
    font-size:12px;
    }
    #grClose::title,#grStop::title{
    color:red;
    }
    #txt1,#txt2,#txt3{
    color:green;
    }
    #txt_c1,#txt_c2,#txt_c3{
    color:red;
    }
    QPushButton
    {
    color:#0000FF;    
    }
    QPushButton:hover 
    {Color:red}
    QPushButton#b_autostop,QPushButton#b_pause
    {
    background-color: none ;
    }
    QComboBox:hover{ color:red; }
    QComboBox::drop-down:hover
    {color:red;}
    '''
    w.setStyleSheet(style)
    w.show()

    if w.automaticallyRefresh:
        IB.run()
    else:
        sys.exit(app.exec_())