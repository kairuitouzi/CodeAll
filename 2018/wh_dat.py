import os
import sys
import time
import win32api
import win32con
import win32gui
import pymouse
import pykeyboard

import redis
import pickle

from datetime import datetime
import pyautogui as pag
from struct import unpack
from collections import namedtuple, deque, OrderedDict
from win32gui import IsWindow, IsWindowEnabled, IsWindowVisible, GetWindowText, EnumWindows
from pymouse import PyMouse
from pykeyboard import PyKeyboard
from ctypes import windll as win32


Red = redis.Redis()  # key whfuture_min1
Min = []

try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BASE_DIR = os.path.join(BASE_DIR, 'AndBefore_2018_3')
    sys.path.append(BASE_DIR)
    from MyUtil import get_conn
except:
    from myconn.myconn import get_conn

"""
读取文华财经dat数据，并存储到数据库
"""


class WHCJ:
    def __init__(self):
        self.conn = get_conn('carry_investment')
        N = namedtuple('N', ['month', 'code'])
        # 代码所对应的合约
        self.hsi = OrderedDict({
            '00034150.dat': N(1, 'HSIF9'),
            '00034151.dat': N(2, 'HSIG9'),
            '00034152.dat': N(3, 'HSIH9'),
            '00034154.dat': N(4, 'HSIJ9'),
            '00034155.dat': N(5, 'HSIK9'),
            '00034157.dat': N(6, 'HSIM9'),
            '00034158.dat': N(7, 'HSIN9'),
            '00034161.dat': N(8, 'HSIQ9'),
            '00034165.dat': N(9, 'HSIU9'),
            '00034166.dat': N(10, 'HSIV9'),
            '00034168.dat': N(11, 'HSIX9'),
            '00034170.dat': N(12, 'HSIZ9'),
        })
        # 7214 # HSI 00034182.dat
        # 7253 # MHI 00034233.dat
        # 7234 # HHI 00034214.dat
        # 恒生期货当月
        self.same_month = {'00034182.dat': 'HSI', '00034233.dat': 'MHI', '00034214.dat': 'HHI'}
        # 恒生指数 HSI, 国内 IF,IH,IC 主连
        self.index = {
            '00033906.dat': 'HSI',
            '00010067.dat': 'IF',
            '00010083.dat': 'IH',
            '00010213.dat': 'IC',
        }

    def transfer_min1(self, files):
        ''' 解析一分钟、五分钟数据 '''
        contrast = None
        with open(files, 'rb') as f:
            buf = f.read()
        num = len(buf)
        no = (num - 4) / 36  # 32
        b = 4  # 0
        e = 40  # 32

        for i in range(int(no) - 1):
            a = unpack('iffffffff', buf[b:e])
            dd = a[0]
            openPrice = a[1]
            close = a[2]
            high = a[3]
            low = a[4]
            vol = a[5]
            amount = a[6]

            dd = datetime.fromtimestamp(dd)

            b += 36  # 32
            e += 36  # 32
            if i != 0:
                t = dd - contrast
                if dd < contrast or t.days > 100:
                    break
                contrast = dd
                yield [dd, openPrice, high, low, close, vol, amount, a[7], a[8]]
            else:
                contrast = dd
                yield [dd, openPrice, high, low, close, vol, amount, a[7], a[8]]

    def transfer_day(self, files):
        ''' 解析日线数据 '''
        contrast = None
        with open(files, 'rb') as f:
            buf = f.read()
        num = len(buf)
        no = num / 37
        b = 0
        e = 37

        for i in range(int(no) - 1):
            a = unpack('iffffffffB', buf[b:e])
            dd = a[0]
            openPrice = a[1]
            close = a[2]
            high = a[3]
            low = a[4]
            vol = a[5]
            amount = a[6]

            dd = datetime.fromtimestamp(dd)

            b += 37  # 32
            e += 37  # 32
            if i != 0:
                t = dd - contrast
                if dd < contrast or t.days > 100:
                    break
                contrast = dd
                yield [dd, openPrice, high, low, close, vol, amount, a[7], a[8]]
            else:
                contrast = dd
                yield [dd, openPrice, high, low, close, vol, amount, a[7], a[8]]

    def to_sql(self, conn, data):
        cur = conn.cursor()
        sql = "INSERT INTO wh_min(prodcode,datetime,open,high,low,close,vol) VALUES(%s,%s,%s,%s,%s,%s,%s)"
        count = 0
        cur.execute("SELECT prodcode,datetime FROM wh_min ORDER BY datetime DESC LIMIT 1")
        d = cur.fetchone()
        for i in data:
            try:
                cur.execute(sql, (i[0], i[1], i[2], i[3], i[4], i[5], i[6]))
            except Exception as exc:
                print(exc)
            count += 1
            if not count % 10000:
                conn.commit()
        else:
            conn.commit()

    def file_to_sql(self, file_path, dat, code_time):
        """ 获得文件数据，插入数据库 """
        global Min
        cur = self.conn.cursor()
        count = 0
        insert_size = 0
        folder = file_path.split('\\')[-2]
        if folder == 'min1' and dat in self.hsi:
            code = self.hsi[dat].code
            next_data = self.transfer_min1(file_path)
            sql = "INSERT INTO wh_min(prodcode,datetime,open,high,low,close,vol,position,settlement,ratio) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        elif folder == 'min1' and dat in self.same_month:
            code = self.same_month[dat]
            next_data = self.transfer_min1(file_path)
            sql = "INSERT INTO wh_same_month_min(prodcode,datetime,open,high,low,close,vol,position,settlement,ratio) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        elif folder == 'min1' and dat in self.index:
            code = self.index[dat]
            next_data = self.transfer_min1(file_path)
            sql = "INSERT INTO wh_index_min(prodcode,datetime,open,high,low,close,vol,position,settlement,ratio) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        elif folder == 'day' and dat in self.same_month:
            code = self.same_month[dat]
            next_data = self.transfer_day(file_path)
            sql = "INSERT INTO wh_same_month_day(prodcode,datetime,open,high,low,close,vol,position,settlement,ratio) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        elif folder == 'min5' and dat in self.same_month:
            code = self.same_month[dat]
            next_data = self.transfer_min1(file_path)
            sql = "INSERT INTO wh_same_month_min5(prodcode,datetime,open,high,low,close,vol,position,settlement,ratio) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        else:
            return None

        # 保存到数据库
        for i in next_data:
            if code_time and i[0] <= code_time[1]:
                continue
            try:
                cur.execute(sql, (code, str(i[0])[:19], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8]))
                insert_size += 1
                if dat == '00034182.dat' and folder == 'min1':
                    Min.append((code, str(i[0])[:19], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8]))
            except Exception as exc:
                print(exc)
            count += 1
            if not count % 10000:
                self.conn.commit()
        if dat == '00034182.dat' and folder == 'min1':
            Min = Min[-100:]  # 限制为只保存100条分钟数据
            Red.set('whfuture_min1', pickle.dumps(Min))
        return insert_size

    def main(self, to_file=None):
        """ to_file: 如果有传入to_file，则只使用to_file这个文件更新数据库，否则检查所有指定文件并更新到数据库"""
        dirs = r'C:\wh6模拟版\Data\恒生期指\min1'

        t = datetime.now()
        hsi = self.hsi
        index = self.index
        same_month = self.same_month
        dat = to_file.split('\\')[-1] if to_file else 0
        folder = to_file.split('\\')[-2] if to_file else ''
        cur = self.conn.cursor()
        if folder == 'min1' and dat in same_month:
            code_time_sql = "SELECT prodcode,datetime FROM wh_same_month_min WHERE prodcode='%s' ORDER BY datetime DESC LIMIT 1" % \
                            same_month[dat]
        elif folder == 'min1' and dat in hsi:
            code_time_sql = "SELECT prodcode,datetime FROM wh_min ORDER BY datetime DESC LIMIT 1"
        elif folder == 'min1' and dat in index:
            code_time_sql = "SELECT prodcode,datetime FROM wh_index_min WHERE prodcode='%s' ORDER BY datetime DESC LIMIT 1" % \
                            index[dat]
        elif folder == 'day' and dat in same_month:
            code_time_sql = "SELECT prodcode,datetime FROM wh_same_month_day ORDER BY datetime DESC LIMIT 1"
        elif folder == 'min5' and dat in same_month:
            code_time_sql = "SELECT prodcode,datetime FROM wh_same_month_min5 ORDER BY datetime DESC LIMIT 1"
        else:
            return
        cur.execute(code_time_sql)
        code_time = cur.fetchone()
        self.conn.commit()

        numbers = [nu for nu in os.listdir(dirs) if (nu in hsi and hsi[nu].month <= t.month) or nu in same_month]

        if to_file:
            insert_size = self.file_to_sql(to_file, dat, code_time)
            self.conn.commit()
            return insert_size

        for number in numbers:
            file_path = dirs + os.sep + number
            insert_size = self.file_to_sql(file_path, dat, code_time)

        self.conn.commit()

        return insert_size

    def sbdj(self, x, y, enter=None):
        """ 鼠标左击 与 按回车键 """
        win32api.SetCursorPos([x, y])  # 为鼠标焦点设定一个位置
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        # win32api.keybd_event(0,0,win32con.KEYEVENTF_KEYUP,0)
        if enter is not None:
            # 按下回车键
            time.sleep(0.1)
            win32api.keybd_event(13, 0, 0, 0)
            win32api.keybd_event(13, 0, win32con.KEYEVENTF_KEYUP, 0)

    def get_ct(self):
        """ 获取所有Windows打开的窗体 """
        titles = set()

        def foo(hwnd, mouse):
            # 去掉下面这句就能获取所有，但是我不需要那么多
            if IsWindow(hwnd) and IsWindowEnabled(hwnd) and IsWindowVisible(hwnd):
                titles.add(GetWindowText(hwnd))

        EnumWindows(foo, 0)
        return titles

    def start_wh(self):
        """ 启动文华财经，并返回窗口句柄"""
        # 启动文华财经
        os.system('start C:\wh6模拟版\mytrader_wh.exe')
        cts = self.get_ct()
        count = 0
        while '赢顺云交易' not in ''.join(cts):  # 若窗口没打开，则过一秒后再次检查
            time.sleep(1)
            count += 1
            cts = self.get_ct()
            if not count % 30:
                os.system('taskkill /F /IM mytrader_wh.exe')
                os.system('start C:\wh6模拟版\mytrader_wh.exe')
        d2 = [i for i in cts if '赢顺云交易' in i][0]
        win = win32gui.FindWindow(None, d2)
        return win

    def runs(self):
        """ 循环点击文华财经以刷新本地文件 """
        win = self.start_wh()
        ct = []
        for i in range(65536):
            tid = win32gui.FindWindowEx(win, None, i, None)
            if tid != 0:
                ct.append(tid)
            if len(ct) == 2:
                break
        hEdit = win32.user32.FindWindowExW(ct[-1], None, 'Edit', None)
        WM_CHAR = 0x0102
        min1_zb = (258, 32)
        # aj=OrderedDict({'wp':(16,330), 'wpzlhy':(906,999), 'hz=':(131,94), 'min1':(260,35), 'back_off':(19,31)})
        x, y = pag.position()  # 原来鼠标坐标
        # win32gui.ShowWindow(win, win32con.SW_MAXIMIZE)  # 全屏
        time.sleep(0.1)
        self.sbdj(*min1_zb)
        time.sleep(0.5)
        win32api.SetCursorPos([x, y])  # 为鼠标还原到原来的坐标
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        win32gui.CloseWindow(win)  # 最小化
        start_time = 0

        # 打开代码为name的产品
        def start_name(name):
            len_name = len(name)
            for i in range(len_name):
                win32.user32.SendMessageW(hEdit, WM_CHAR, ord(name[i]), None)
                time.sleep(0.05)
                if i == len_name - 1:
                    time.sleep(0.1)
                    try:
                        # 进行回车确认
                        # win32gui.SetForegroundWindow(hEdit)
                        # win32api.keybd_event(13, 0, 0, 0)
                        # win32api.keybd_event(13, 0, win32con.KEYEVENTF_KEYUP, 0)
                        win32gui.PostMessage(hEdit, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
                        win32gui.PostMessage(hEdit, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
                    except:
                        self.runs()

        while 1:
            t2 = time.time()
            t = time.localtime(t2)
            t_min = t.tm_hour * 60 + t.tm_min
            if t.tm_hour == 12 or (16 * 60 + 30 < t_min < 17 * 60 + 15) or (0 < t_min < 9 * 60 + 15):
                continue

            # 要更新的产品代码
            names = {'7204': 'HSIJ9', '7121': 'HSI', '7253': 'MHI',
                     '7234': 'HHI', '8618': 'IF',
                     '8633': 'IH', '8693': 'IC', '7214': 'HSI'}
            for name in names:
                if name not in {'7253', '7214'}:
                    if t2 - start_time < 600:
                        continue
                    elif name in {'8618', '8633', '8693'} and t.tm_hour > 14:
                        continue
                    else:
                        start_time = 1
                print('更新产品：', name, names[name], '...')
                start_name(name)
                time.sleep(5)
            # win32gui.SetForegroundWindow(win) # 指定句柄设置为前台，也就是激活
            # win32gui.SetBkMode(win, win32con.TRANSPARENT) # 设置为后台
            start_time = t2 if start_time == 1 else start_time
            time.sleep(60)


if __name__ == '__main__':
    # res = main(d)
    # with open('res.txt','w') as f:
    #	f.write(json.dumps(res))
    # to_sql(conn,res[:-1])
    whcj = WHCJ()
    print(whcj.main())
