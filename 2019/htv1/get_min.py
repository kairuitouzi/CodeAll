import os, time, pymysql, configparser
from datetime import datetime
from tkinter import *
from tkinter.messagebox import showinfo
from tkinter import messagebox


class Note:
    def __init__(self):

        self.root = Tk()  # 用库中的 Tk() 方法创建主窗口，并把窗口名称赋值给 root
        self.root.title("指数分钟K线")
        self.root.geometry("600x400+100+100")
        self.textpad = Text(self.root, undo=True, font=('华康少女字体', 12), bg='black',fg='green')
        self.textpad.pack(expand=YES, fill=BOTH)
        self.isRun = True
        try:
            config = configparser.ConfigParser()
            config.read('index_conf.conf')
            host = config['MINK']['host']
            port = config['MINK']['port']
            user = config['MINK']['user']
            passwd = config['MINK']['passwd']
            db_name = config['MINK']['db']
            self.min_input = config['MINK']['filedir']
        except:
            host = 'kairuiserver'
            port = '3306'
            user = 'kairuitouzi'
            passwd = 'kairuitouzi'
            db_name = 'stock_data'
            self.min_input = 'D:\\同花顺软件\\同花顺港股版\\history\hz\min\\'
            #self.min_input='C:\\Users\\Administrator\\Desktop\\Tools\\2017-12-18\\min\\'
        self.conn = pymysql.connect(host=host, db=db_name, user=user, passwd=passwd, port=int(port))
        # self.conn = pymysql.connect(db='stockDate', user='root', passwd='123456')
        self.textpad.insert(1.0, '您好! 欢迎使用!')
        # min_input = r'C:\Users\Administrator\Desktop\Tools\2017年12月12日\min\\'

    def read_zhishu_min(self, min_input, filename):
        file_object = open(min_input + filename, 'rb')
        try:
            txt = file_object.read()
            NumberOfRecords0 = txt[6]
            NumberOfRecords1 = txt[7] * 256
            NumberOfRecords2 = txt[8] * 256 * 256
            NumberOfRecords3 = txt[9] * 256 * 256 * 256
            NumberOfRecords0 = NumberOfRecords0 + NumberOfRecords1 + NumberOfRecords2 + NumberOfRecords3

            RecordTheStartPosition = txt[10] + txt[11] * 256
            # print("记录开始位置=" , RecordTheStartPosition)
            TheLengthOfEachRecord = txt[12] + txt[13] * 256
            # print("每记录的长度=" , TheLengthOfEachRecord)
            j = 1
            IndependentVariableX = 1 + RecordTheStartPosition + TheLengthOfEachRecord * (
            NumberOfRecords0 - 1)  # 最后的一条记录
            code = filename.split('.')[0]
            cur = self.conn.cursor()
            cur.execute('select datetime from min_last_date where code="%s"' % code)
            isInsert = False
            try:
                last_date = cur.fetchone()[0]
            except:
                isInsert = True
                last_date = datetime(1990, 1, 1)
            if not last_date:
                last_date = datetime(1990, 1, 1)
            try:
                cur.execute('DELETE FROM index_min WHERE code="%s" AND datetime="%s"' % (code, last_date))
            except:
                pass
            while j <= NumberOfRecords0:  # 2
                zhongji = list()
                # 时间处理
                IndependentVariableY0 = txt[IndependentVariableX - 1]
                IndependentVariableY1 = txt[IndependentVariableX]
                IndependentVariableY1 = IndependentVariableY1 * 256
                IndependentVariableY2 = txt[IndependentVariableX + 1]
                IndependentVariableY2 = IndependentVariableY2 * 256 * 256
                IndependentVariableY3 = txt[IndependentVariableX + 2]
                IndependentVariableY3 = IndependentVariableY3 * 256 * 256 * 256
                IndependentVariableY0 = IndependentVariableY0 + IndependentVariableY1 + IndependentVariableY2 + IndependentVariableY3

                Times = list()
                Times.append(int(IndependentVariableY0 / 1048576) + 1900)  # yyyy-
                Times.append(int((IndependentVariableY0 % 1048576) / 65536))  # yyyy-mm-
                Times.append(int((IndependentVariableY0 % 65536) / 2048))  # yyyy-mm-dd
                Times.append(int((IndependentVariableY0 % 2048) / 64))  # yyyy-mm-dd-hh:
                Times.append(IndependentVariableY0 % 64)  # yyyy-mm-dd-hh-mm
                if datetime(Times[0], Times[1], Times[2], Times[3], Times[4]) < last_date:
                    break

                zhongji.append(datetime(Times[0], Times[1], Times[2], Times[3], Times[4]))
                # 开盘价
                IndependentVariableY0 = txt[IndependentVariableX + 3]
                IndependentVariableY1 = txt[IndependentVariableX + 4]
                IndependentVariableY1 = IndependentVariableY1 * 256
                IndependentVariableY2 = txt[IndependentVariableX + 5]
                IndependentVariableY2 = IndependentVariableY2 * 256 * 256
                IndependentVariableY3 = txt[IndependentVariableX + 6]
                IndependentVariableY3 = IndependentVariableY3 % 16
                IndependentVariableY3 = IndependentVariableY3 * 256 * 256 * 256
                IndependentVariableY0 = IndependentVariableY0 + IndependentVariableY1 + IndependentVariableY2 + IndependentVariableY3

                TimeProcessing = ""
                TimeProcessing = TimeProcessing + str(int(IndependentVariableY0 / 1000))  # 整数位
                TimeProcessing = TimeProcessing + "."
                TimeProcessing = TimeProcessing + str(int(IndependentVariableY0 % 1000))  # 小数位

                zhongji.append(TimeProcessing)
                # 最高价
                IndependentVariableY0 = txt[IndependentVariableX + 7]
                IndependentVariableY1 = txt[IndependentVariableX + 8]
                IndependentVariableY1 = IndependentVariableY1 * 256
                IndependentVariableY2 = txt[IndependentVariableX + 9]
                IndependentVariableY2 = IndependentVariableY2 * 256 * 256
                IndependentVariableY3 = txt[IndependentVariableX + 10]
                IndependentVariableY3 = IndependentVariableY3 % 16
                IndependentVariableY3 = IndependentVariableY3 * 256 * 256 * 256
                IndependentVariableY0 = IndependentVariableY0 + IndependentVariableY1 + IndependentVariableY2 + IndependentVariableY3

                TimeProcessing = ""
                TimeProcessing = TimeProcessing + str(int(IndependentVariableY0 / 1000))  # 整数位
                TimeProcessing = TimeProcessing + "."
                TimeProcessing = TimeProcessing + str(int(IndependentVariableY0 % 1000))  # 小数位

                zhongji.append(TimeProcessing)
                # 最低价
                IndependentVariableY0 = txt[IndependentVariableX + 11]
                IndependentVariableY1 = txt[IndependentVariableX + 12]
                IndependentVariableY1 = IndependentVariableY1 * 256
                IndependentVariableY2 = txt[IndependentVariableX + 13]
                IndependentVariableY2 = IndependentVariableY2 * 256 * 256
                IndependentVariableY3 = txt[IndependentVariableX + 14]
                IndependentVariableY3 = IndependentVariableY3 % 16  # 防溢出处理，同时也将最高位的XY中的X修改为0
                IndependentVariableY3 = IndependentVariableY3 * 256 * 256 * 256
                IndependentVariableY0 = IndependentVariableY0 + IndependentVariableY1 + IndependentVariableY2 + IndependentVariableY3

                TimeProcessing = ""
                TimeProcessing = TimeProcessing + str(int(IndependentVariableY0 / 1000))  # 整数位
                TimeProcessing = TimeProcessing + "."
                TimeProcessing = TimeProcessing + str(int(IndependentVariableY0 % 1000))  # 小数位

                zhongji.append(TimeProcessing)

                # 收盘价
                IndependentVariableY0 = txt[IndependentVariableX + 15]
                IndependentVariableY1 = txt[IndependentVariableX + 16]
                IndependentVariableY1 = IndependentVariableY1 * 256
                IndependentVariableY2 = txt[IndependentVariableX + 17]
                IndependentVariableY2 = IndependentVariableY2 * 256 * 256
                IndependentVariableY3 = txt[IndependentVariableX + 18]
                IndependentVariableY3 = IndependentVariableY3 % 16
                IndependentVariableY3 = IndependentVariableY3 * 256 * 256 * 256
                IndependentVariableY0 = IndependentVariableY0 + IndependentVariableY1 + IndependentVariableY2 + IndependentVariableY3

                TimeProcessing = ""
                TimeProcessing = TimeProcessing + str(int(IndependentVariableY0 / 1000))  # 整数位
                TimeProcessing = TimeProcessing + "."
                TimeProcessing = TimeProcessing + str(int(IndependentVariableY0 % 1000))  # 小数位

                zhongji.append(TimeProcessing)
                # 成交额
                IndependentVariableY0 = txt[IndependentVariableX + 19]
                IndependentVariableY1 = txt[IndependentVariableX + 20]
                IndependentVariableY1 = IndependentVariableY1 * 256
                IndependentVariableY2 = txt[IndependentVariableX + 21]
                IndependentVariableY2 = IndependentVariableY2 * 256 * 256
                IndependentVariableY3 = txt[IndependentVariableX + 22]
                IndependentVariableY3 = IndependentVariableY3 % 16  # 防溢出处理，同时也将最高位的XY中的X修改为0
                IndependentVariableY3 = IndependentVariableY3 * 256 * 256 * 256
                IndependentVariableY0 = IndependentVariableY0 + IndependentVariableY1 + IndependentVariableY2 + IndependentVariableY3

                IndependentVariableY0 = IndependentVariableY0 * 10

                zhongji.append(IndependentVariableY0)

                # 成交量股
                IndependentVariableY0 = txt[IndependentVariableX + 23]
                IndependentVariableY1 = txt[IndependentVariableX + 24]
                IndependentVariableY1 = IndependentVariableY1 * 256
                IndependentVariableY2 = txt[IndependentVariableX + 25]
                IndependentVariableY2 = IndependentVariableY2 * 256 * 256
                IndependentVariableY3 = txt[IndependentVariableX + 26]
                IndependentVariableY3 = IndependentVariableY3 % 16  # 防溢出处理，同时也将最高位的XY中的X修改为0
                IndependentVariableY3 = IndependentVariableY3 * 256 * 256 * 256
                IndependentVariableY0 = IndependentVariableY0 + IndependentVariableY1 + IndependentVariableY2 + IndependentVariableY3

                zhongji.append(IndependentVariableY0)
                zhongji.append(isInsert)
                yield zhongji
                IndependentVariableX = IndependentVariableX - TheLengthOfEachRecord
                j += 1
        except Exception as exc:
            print(exc)
            return []
        finally:
            file_object.close()

    def opens(self, event=None):
        self.isRun = True
        conn = self.conn
        min_input = self.min_input
        try:
            fileUpdateTime = {i: 0 for i in os.listdir(min_input)}
        except:
            messagebox.showerror('错误','%s 路径有误！\n请在配置文件index_conf.conf的[MINK]标签下修改filedir = C:\\x\\x\\' % min_input)
            return
        while self.isRun:
            # min文件目录
            filename = os.listdir(min_input)
            i = 0
            while i < len(filename):
                strx = filename[i]
                isTime = os.path.getmtime(min_input + strx)
                try:
                    if fileUpdateTime[strx] == isTime:
                        i += 1
                        continue
                except:
                    fileUpdateTime[strx] = isTime
                fileUpdateTime[strx] = isTime
                cur = conn.cursor()
                code = strx.split('.')[0]
                x = 0
                this_time = 0
                try:
                    for rows in self.read_zhishu_min(min_input, strx):
                        if x is 0:
                            this_time = rows[0]
                            if rows[7]:
                                cur.execute('insert into min_last_date(datetime,code) values(%s,%s)', (rows[0], code))
                            else:
                                cur.execute('update min_last_date set datetime="%s" WHERE code="%s"' % (rows[0], code))

                        try:
                            cur.execute(
                                'insert into index_min(code,datetime,open,high,low,close,amount,vol) values(%s,%s,%s,%s,%s,%s,%s,%s)',
                                (code, rows[0], float(rows[1]), float(rows[2]), float(rows[3]), float(rows[4]),int(rows[5]),int(rows[6])))
                        except:
                            try:
                                cur.execute(
                                    'update index_min set open=%s,high=%s,low=%s,close=%s,amount=%s,vol="%s" WHERE code="%s" AND datetime="%s"' % (
                                        float(rows[1]), float(rows[2]), float(rows[3]), float(rows[4]), int(rows[5]),int(rows[6]), code, rows[0]))
                            except:
                                conn.rollback()
                                self.textpad.insert(1.0, '%s 数据格式不合适\n' % strx)
                                self.textpad.update()
                                break
                        x += 1
                    conn.commit()
                except:
                    conn.rollback()
                    self.textpad.insert(1.0, '%s 数据格式不合适\n' % strx)
                    self.textpad.update()
                    return
                i += 1
                prints = '文件：%s,  Last Time: %s\n' % (strx, this_time)
                self.textpad.insert(1.0, prints)
                self.textpad.update()

            self.textpad.update()
            time.sleep(2)
        conn.close()

    def tuichu(self, q=None):
        self.conn.close()
        self.root.quit()
    def deletes(self):
        if messagebox.askokcancel('删除提示', '确定要删除所有数据吗？'):
            conn=self.conn
            cur=conn.cursor()
            try:
                cur.execute('DELETE FROM index_min')
                cur.execute('DELETE FROM min_last_date')
            except:
                conn.rollback()
                self.textpad.insert(1.0,'删除失败！请检测数据库连接信息是否正确或重新启动再进行删除！\n')
                self.textpad.update()
            else:
                conn.commit()
                self.textpad.insert(1.0, '删除成功！\n')
                self.textpad.update()

    def stops(self, t=None):
        self.isRun = False

    def about(self):
        showinfo('版权信息', '凯瑞投资有限公司!')

    def help(self):
        showinfo('帮助信息', '配置文件：index_conf.conf\n默认数据库：stock_data\n默认数据表：index_min，min_last_date!')

    def main(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        filemenu = Menu(menubar)
        filemenu.add_command(label='开始', accelerator='ctrl+O', command=self.opens)
        filemenu.add_command(label='停止', accelerator='Ctrl+t', command=self.stops)
        filemenu.add_command(label='退出', accelerator='Ctrl+q', command=self.tuichu)
        filemenu.add_command(label='删除', command=self.deletes)
        menubar.add_cascade(label='操作', menu=filemenu)
        self.root.bind_all('<Control-o>', self.opens)  # 开始
        self.root.bind('<Control-t>', self.stops)
        self.root.bind('<Control-q>', self.tuichu)  # 退出

        # 关于
        aboutmenu = Menu(menubar)

        aboutmenu.add_command(label='版权', command=self.about)
        aboutmenu.add_command(label='帮助', command=self.help)
        menubar.add_cascade(label='关于', menu=aboutmenu)

        # 正文编辑区
        lnlabel = Label(self.root, width=2)
        lnlabel.pack(side=LEFT, fill=Y)

        scroll = Scrollbar(self.textpad)
        self.textpad.config(yscrollcommand=scroll.set)
        scroll.config(command=self.textpad.yview)
        scroll.pack(side=RIGHT, fill=Y)

        self.root.mainloop()


if __name__ == '__main__':
    Note().main()
