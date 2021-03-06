import requests
import re
import time
import datetime
import matplotlib
from pylab import mpl
from threading import Thread
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import tkinter as tk
import pymysql
import inspect
import ctypes
#from tkinter import *



def _async_raise(tid, exctype):
    """关闭线程"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        pass #print('没有启动') #raise ValueError("invalid thread id")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
    return res


def stop_thread(thread):
    """用来被调用，关闭线程"""
    return _async_raise(thread.ident, SystemExit)

#matplotlib.use('TkAgg')

class Application(tk.Tk):
    '''
    权重股图
    '''

    def __init__(self):
        '''初始化'''
        super().__init__()  # 有点相当于tk.Tk()
        self.isRun=False
        self.isRun_p=False
        self.sleeps=10
        self.weight=('汇丰控股', '腾讯控股', '友邦保险', '建设银行', '中国移动', '工商银行', '中国平安', '中国银行')  #权重比重最大
        self.drawPic()
        try:
            self.conn = pymysql.connect(host='192.168.2.226', user='kairuitouzi', passwd='kairuitouzi', charset='utf8',
                                   port=3306, db='stock_data')
        except Exception as exc:
            print(exc)

    def bar3dTime(self):
        self.topsearch=tk.Toplevel(master=self.footframe)
        self.topsearch.geometry('300x30+200+250')
        self.topsearch.title('输入时间')
        label1=tk.Label(self.topsearch,text='请输入开始时间')
        label1.grid(row=0,column=0,padx=5)
        self.entry1=tk.Entry(self.topsearch,width=20)
        self.entry1.grid(row=0,column=1,padx=5)
        button1=tk.Button(self.topsearch,text='确定',command=self.bar_3d)
        button1.grid(row=0,column=2)

    def bar_3d(self):

        '''ti=self.entry1.get().split()[0]
        ti=re.findall('(\d+)',ti)
        ti=''.join(ti)[:4]
        self.topsearch.destroy()  #关闭时间输入框
        self.isRun_p=False'''

        names = ('汇丰控股','腾讯控股','友邦保险','建设银行','中国移动','工商银行','中国平安','中国银行', '香港交易所',
                 '长和', '中国海洋石油', '中国人寿', '长实集团', '新鸿基地产', '领展房产基金')
        names1=['\n'.join(i) for i in names]
        #times=datetime.datetime.strptime(str(datetime.datetime.now())[:11]+ti[:2]+':'+ti[2:]+':00','%Y-%m-%d %H:%M:%S')
        #_times=times+datetime.timedelta(minutes=30)
        _times=datetime.datetime.now()
        times=_times-datetime.timedelta(minutes=30)
        print(times)
        cur=self.conn.cursor()
        cur.execute(f'select number,name,time from weight where name in {names} and time>="{times}" and time<="{_times}"')
        result = cur.fetchall()
        self.conn.commit()
        clr = ['#4bb2c5', '#c5b47f', '#EAA228', '#579575', '#839557', '#958c12', '#953579', '#4b5de4']
        color_type = lambda x: ['green' if i < 0 else 'red' for i in x]
        fig = plt.figure()
        fig.set_size_inches(16, 8)  # 设置显示的图片大小
        ax = Axes3D(fig)
        x = np.arange(len(names))
        z = [int(str(i[2])[-8:].replace(':', '')[:4]) for i in result if i[1] == names[0]]
        z2 = [i[2] for i in result if i[1] == names[0]]
        for inds, zs in enumerate(z2):

            y = [i[0] for i in result if i[1] in names and i[2] == z2[inds]]

            if len(y) != len(names):
                continue
            ax.bar(names1, y, z[inds], zdir='y', color=color_type(y),width=0.2)
        '''
        ax.bar(x, y, 0, zdir='y', color=clr)
        ax.bar(x, y2, 10, zdir='y', color=clr)
        ax.bar(x, y3, 20, zdir='y', color=clr)
        ax.bar(x, y4, 30, zdir='y', color=clr)
        ax.bar(x, y5, 40, zdir='y', color=clr)'''
        ax.set_xlabel('名称（X）',fontdict={'color':'blue'})
        ax.set_ylabel('时间（Y）',fontdict={'color':'green'})
        ax.set_zlabel('点数（Z）',fontdict={'color':'red'})
        ax.view_init(elev=75)
        plt.show()

    def plot_show(self):
        '''根据恒生指数成分股数据画出条形图，属于动态图'''
        fig, ax = plt.subplots()
        fig.set_size_inches(16, 8)  # 设置显示的图片大小

        color_type = lambda x: 'blue' if x[1] in self.weight else ('green' if x[0] < 0 else 'red')
        #self.isRun=False
        #while self.isRun_p:
        try:
            result, times = self.get_data()
        except Exception as exc:
            print(exc)
            return
            #time.sleep(18)

        x = ['\n'.join(i[1].replace('\'', '').replace('A', '')) for i in result]
        y = [i[0] for i in result]
        ind = np.arange(len(x))
        ax.cla()  # 清除之前的图形
        ax.bar(ind, y, color=[color_type(i) for i in result], edgecolor='white')  # color条形颜色
        ax.grid(axis='y',linestyle='-.')
        plt.xticks(ind, x, fontsize=10, color='green')  # fontsize字体大小，color字体颜色，rotation=270 旋转度数
        plt.title(f'恒生指数成分股（{len(x)}）- - {times}')
        #for x,y in zip(ind,x):
        #    plt.text(x,y,'%s'%y,ha='center',va='bottom')
        ax.legend()
        plt.show()
        #plt.pause(10)  # 每隔一秒刷新一次

    def zhexian(self):
        self.isRun_p = False
        names=('汇丰控股','腾讯控股','友邦保险','建设银行','中国移动','工商银行','中国平安','中国银行')
        mar=['o','v','>','<','.','s','*','+']
        cur=self.conn.cursor()
        cur.execute(f'select number,name,time from weight where name in {names}')
        result =cur.fetchall()
        self.conn.commit()
        print(result[-1])
        fig, ax = plt.subplots()
        fig.set_size_inches(16, 8)  # 设置显示的图片大小

        for inds in range(len(names)):
            x=[i[2] for i in result if i[1]==names[inds]]
            y=[i[0] for i in result if i[1]==names[inds]]

            # y1 = [10, 13, 5, 40, 30, 60, 70, 12, 55, 25]
            # x1 = range(0, 10)
            # x2 = range(0, 10)
            # y2 = [5, 8, 0, 30, 20, 40, 50, 10, 40, 15]
            #plt.plot(x1, y1, label='Frist line', linewidth=3, color='r', marker='o',
            #         markerfacecolor='blue', markersize=12)
            plt.plot(x,y ,label=names[inds],marker=mar[inds])

            #cou+=1
            #if cou>=10: break
        plt.xlabel('时间')
        plt.ylabel('点数')
        plt.title('恒生指数8大成分股折线图')
        plt.legend()
        plt.show()

    def plot_show_thr(self):
        '''外图，实时刷新用的'''
        self.isRun_p = False if self.isRun_p else True
        if not self.isRun_p: return
        t=Thread(target=self.plot_show,args=())
        t.setDaemon(True)
        t.start()

    def drawPic(self):
        '''根据恒生指数成分股数据画出条形图，属于动态图'''
        self.fig = Figure(figsize=(16, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        toolbar.update()
        footframe = tk.Frame(master=self).pack(side=tk.BOTTOM)
        self.footframe=footframe

        tk.Button(master=footframe, text='3D', command=self.bar_3d,bg='green').pack(side=tk.RIGHT,expand=1, pady=2) #side=tk.BOTTOM)
        tk.Button(master=footframe, text='退出', command=self._quit,bg='red').pack(side=tk.RIGHT,expand=1, pady=2) #side=tk.BOTTOM)
        tk.Button(master=footframe,text='排序',command=self.plot_show,bg='green').pack(side=tk.RIGHT,expand=1, pady=2) #side=tk.BOTTOM)
        tk.Button(master=footframe,text='折线图',command=self.zhexian,bg='green').pack(side=tk.RIGHT,expand=1, pady=2)
        tk.Button(master=footframe,text='刷新',command=self.update_sleep,bg='green').pack(side=tk.RIGHT,expand=1, pady=1)


        mpl.rcParams['font.sans-serif'] = ['FangSong']  # 指定默认字体
        mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

        self.tk_show_thread()  # 绘图

        # rdm = random.randint
        # result = get_date()
        # result = [(i[0] + rdm(-10, 10), i[1]) for i in result]  # 模拟数据变化



        # plt.xticks(ind,x)

        # drawPic.patch.set_facecolor("white")  # 设置背景颜色
        # drawPic.title(f'恒生指数成分股（{len(x)}）')
        # pt.grid(True, linestyle='-.')  #网格, color='r', linewidth='3'
    def update_sleep(self):
        res=stop_thread(self.threads)  #关闭线程
        #print(res)
        self.tk_show_thread()  #重新启动线程

    def tk_show_thread(self):
        self.threads = Thread(target=self.tk_show, args=(), name='get_date')
        self.threads.setDaemon(True)
        self.threads.start()

    def tk_show(self):
        self.isRun=False if self.isRun else True
        while self.isRun:
            self.sleeps=10 if not self.sleeps else self.sleeps
            try:
                result,times = self.get_data()
                self.wm_title("恒生指数成分股（{}）-- {}".format(len(result),times))
            except Exception as exc:
                print(exc)
                time.sleep(12)
                continue
            ax = self.ax
            ax.clear()
            color_type = lambda x: 'blue' if x[1] in self.weight else ('green' if x[0] < 0 else 'red')
            x = ['\n'.join(i[1].replace('\'', '').replace('A', '')) for i in result]
            y = [i[0] for i in result]
            x1 = [i[1] for i in result]
            print(x1)
            print(y)
            ind = np.arange(len(x))
            ax.bar(x, y, color=[color_type(i) for i in result])  # color条形颜色
            #ax.invert_xaxis()
            # ax.set_facecolor('black')
            # ax.set_xticks(x)

            # ax.set_xticklabels(x,colors='red')


            # matplotlib.pyplot.xticks(ind, x, fontsize=10,color='green')  # fontsize=10, color='green' fontsize字体大小，color字体颜色，rotation=270 旋转度数
            ax.grid(axis='y', linestyle='-.')


            self.canvas.show()
            time.sleep(self.sleeps)


    def _quit(self):
        '''退出'''
        self.isRun=False
        self.isRun_p=False
        try: self.conn.close()
        except Exception as exc: print(exc)
        self.quit()  # 停止 mainloop
        self.destroy()  # 销毁所有部件

    def get_data(self, url=None):
        '''获取恒生指数成分股数据，格式为：
        [(34, '腾讯控股'), (27, '香港交易所'), (21, '建设银行'), (18, '中国银行'), (16, '工商银行')...]'''

        url = url if url else 'http://sc.hangseng.com/gb/www.hsi.com.hk/HSI-Net/HSI-Net?cmd=nxgenindex&index=00001&sector=00'
        req = requests.get(url).text
        req = re.sub('\s', '', req)
        # req=re.findall('<constituentscount="51">(.*?)</stock></constituents><isContingency>',req)
        com = re.compile('contribution="([+|-]*\d+)".*?<name>.*?</name><cname>(.*?)</cname></stock>')
        s = re.findall(com, req)
        rq = str(datetime.datetime.now())[:11]
        ti = re.findall('datetime="(.*?)"current', req)[0][-8:]
        s1 = rq + ti  #时间
        # print(s)
        result = [(int(i[0]), i[1]) for i in s if i[0] != '0']
        result.sort()
        result.reverse()
        return result,s1

        #return [(34, '腾讯控股'), (27, '香港交易所'), (21, '建设银行'), (18, '中国银行'), (16, '工商银行')],str(datetime.datetime.now())


if __name__ == '__main__':
    app = Application()
    app.mainloop()


