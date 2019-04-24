import os, time, pymysql, configparser
from datetime import datetime
from tkinter import *
from tkinter.messagebox import showinfo
from tkinter import messagebox
import threading
import logging
import MyUtil

#日志文件名称
log_filename='logging.log'
#日志格式
log_format='%(filename)s[%(asctime)s][%(levelname)s]：%(message)s'
#日志配置
logging.basicConfig(filename=log_filename,filemode='a',level=logging.INFO,datefmt='%Y-%m-%d %H:%M:%S',format=log_format)

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
            self.conn = pymysql.connect(host=host, db=db_name, user=user, passwd=passwd, port=int(port))
        except:
            self.min_input = '\\\\Seo3\\同花顺港股版\\history\\hz\\min\\' #'D:\\同花顺软件\\同花顺港股版\\history\hz\min\\'
            self.conn = MyUtil.get_conn('stock_data')
            #self.min_input='D:\\tools\\Tools\\2017年12月\\2017-12-18\\min\\'

        # self.conn = pymysql.connect(db='stockDate', user='root', passwd='123456')
        logging.info('程序开始。。。')
        self.textpad.insert(1.0, '您好! 欢迎使用!')
        # min_input = r'C:\Users\Administrator\Desktop\Tools\2017年12月12日\min\\'

    def read_zhishu_min(self, min_input, filename):
        file_object = open(min_input + filename, 'rb')
        try:
            txt = file_object.read()
            n0 = txt[6]
            n1 = txt[7] * 256
            n2 = txt[8] * 256 * 256
            n3 = txt[9] * 256 * 256 * 256
            n0 = n0 + n1 + n2 + n3

            rtp = txt[10] + txt[11] * 256
            # print("记录开始位置=" , rtp)
            TheLengthOfEachRecord = txt[12] + txt[13] * 256
            # print("每记录的长度=" , TheLengthOfEachRecord)
            j = 1
            idvx = 1 + rtp + TheLengthOfEachRecord * (
            n0 - 1)  # 最后的一条记录
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
            while j <= n0:  # 2
                zhongji = list()
                # 时间处理
                idvy0 = txt[idvx - 1]
                idvy1 = txt[idvx]
                idvy1 = idvy1 * 256
                idvy2 = txt[idvx + 1]
                idvy2 = idvy2 * 256 * 256
                idvy3 = txt[idvx + 2]
                idvy3 = idvy3 * 256 * 256 * 256
                idvy0 = idvy0 + idvy1 + idvy2 + idvy3

                Times = list()
                Times.append(int(idvy0 / 1048576) + 1900)  # yyyy-
                Times.append(int((idvy0 % 1048576) / 65536))  # yyyy-mm-
                Times.append(int((idvy0 % 65536) / 2048))  # yyyy-mm-dd
                Times.append(int((idvy0 % 2048) / 64))  # yyyy-mm-dd-hh:
                Times.append(idvy0 % 64)  # yyyy-mm-dd-hh-mm
                #if datetime(Times[0], Times[1], Times[2], Times[3], Times[4]) < last_date:
                #    break

                zhongji.append(datetime(Times[0], Times[1], Times[2], Times[3], Times[4]))
                # 开盘价
                idvy0 = txt[idvx + 3]
                idvy1 = txt[idvx + 4]
                idvy1 = idvy1 * 256
                idvy2 = txt[idvx + 5]
                idvy2 = idvy2 * 256 * 256
                idvy3 = txt[idvx + 6]
                idvy3 = idvy3 % 16
                idvy3 = idvy3 * 256 * 256 * 256
                idvy0 = idvy0 + idvy1 + idvy2 + idvy3

                tps = ""
                tps = tps + str(int(idvy0 / 1000))  # 整数位
                tps = tps + "."
                tps = tps + str(int(idvy0 % 1000))  # 小数位

                zhongji.append(tps)
                # 最高价
                idvy0 = txt[idvx + 7]
                idvy1 = txt[idvx + 8]
                idvy1 = idvy1 * 256
                idvy2 = txt[idvx + 9]
                idvy2 = idvy2 * 256 * 256
                idvy3 = txt[idvx + 10]
                idvy3 = idvy3 % 16
                idvy3 = idvy3 * 256 * 256 * 256
                idvy0 = idvy0 + idvy1 + idvy2 + idvy3

                tps = ""
                tps = tps + str(int(idvy0 / 1000))  # 整数位
                tps = tps + "."
                tps = tps + str(int(idvy0 % 1000))  # 小数位

                zhongji.append(tps)
                # 最低价
                idvy0 = txt[idvx + 11]
                idvy1 = txt[idvx + 12]
                idvy1 = idvy1 * 256
                idvy2 = txt[idvx + 13]
                idvy2 = idvy2 * 256 * 256
                idvy3 = txt[idvx + 14]
                idvy3 = idvy3 % 16  # 防溢出处理，同时也将最高位的XY中的X修改为0
                idvy3 = idvy3 * 256 * 256 * 256
                idvy0 = idvy0 + idvy1 + idvy2 + idvy3

                tps = ""
                tps = tps + str(int(idvy0 / 1000))  # 整数位
                tps = tps + "."
                tps = tps + str(int(idvy0 % 1000))  # 小数位

                zhongji.append(tps)

                # 收盘价
                idvy0 = txt[idvx + 15]
                idvy1 = txt[idvx + 16]
                idvy1 = idvy1 * 256
                idvy2 = txt[idvx + 17]
                idvy2 = idvy2 * 256 * 256
                idvy3 = txt[idvx + 18]
                idvy3 = idvy3 % 16
                idvy3 = idvy3 * 256 * 256 * 256
                idvy0 = idvy0 + idvy1 + idvy2 + idvy3

                tps = ""
                tps = tps + str(int(idvy0 / 1000))  # 整数位
                tps = tps + "."
                tps = tps + str(int(idvy0 % 1000))  # 小数位

                zhongji.append(tps)
                # 成交额
                idvy0 = txt[idvx + 19]
                idvy1 = txt[idvx + 20]
                idvy1 = idvy1 * 256
                idvy2 = txt[idvx + 21]
                idvy2 = idvy2 * 256 * 256
                idvy3 = txt[idvx + 22]
                idvy3 = idvy3 % 16  # 防溢出处理，同时也将最高位的XY中的X修改为0
                idvy3 = idvy3 * 256 * 256 * 256
                idvy0 = idvy0 + idvy1 + idvy2 + idvy3

                idvy0 = idvy0 * 10

                zhongji.append(idvy0)

                # 成交量股
                idvy0 = txt[idvx + 23]
                idvy1 = txt[idvx + 24]
                idvy1 = idvy1 * 256
                idvy2 = txt[idvx + 25]
                idvy2 = idvy2 * 256 * 256
                idvy3 = txt[idvx + 26]
                idvy3 = idvy3 % 16  # 防溢出处理，同时也将最高位的XY中的X修改为0
                idvy3 = idvy3 * 256 * 256 * 256
                idvy0 = idvy0 + idvy1 + idvy2 + idvy3

                zhongji.append(idvy0)
                zhongji.append(isInsert)
                yield zhongji
                idvx = idvx - TheLengthOfEachRecord
                j += 1
        except Exception as exc:
            logging.error(exc)
            return []
        finally:
            file_object.close()

    def opens(self, event=None):
        self.isRun = True
        conn = self.conn
        min_input = self.min_input
        #self.to_sql_data(add=False)
        try:
            fileUpdateTime = {i: 0 for i in os.listdir(min_input)}
        except:
            messagebox.showerror('错误','%s 路径有误！\n请在配置文件index_conf.conf的[MINK]标签下修改filedir = C:\\x\\x\\' % min_input)
            return
        while self.isRun:
            # min文件目录
            filename=['HSIc1.min','HSIc2.min','HSIc3.min','HSIc4.min','HHIc1.min','HHIc2.min','HHIc3.min','HHIc4.min']  # filename = os.listdir(min_input)
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
                            cur.execute(
                                'insert into index_backup(code,datetime,open,high,low,close,amount,vol) values(%s,%s,%s,%s,%s,%s,%s,%s)',
                                (code, rows[0], float(rows[1]), float(rows[2]), float(rows[3]), float(rows[4]),
                                 int(rows[5]), int(rows[6])))
                        except:
                            try:
                                cur.execute(
                                    'update index_min set open=%s,high=%s,low=%s,close=%s,amount=%s,vol="%s" WHERE code="%s" AND datetime="%s"' % (
                                        float(rows[1]), float(rows[2]), float(rows[3]), float(rows[4]), int(rows[5]),int(rows[6]), code, rows[0]))
                                cur.execute(
                                    'update index_backup set open=%s,high=%s,low=%s,close=%s,amount=%s,vol="%s" WHERE code="%s" AND datetime="%s"' % (
                                        float(rows[1]), float(rows[2]), float(rows[3]), float(rows[4]), int(rows[5]),
                                        int(rows[6]), code, rows[0]))
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
                # 保存到合并数据表
                if strx=='HSIc1.min':
                    self.to_sql_data(add=True, start_time=this_time, end_time=str(datetime.now()))

            self.textpad.update()
            time.sleep(2)


    def thread_opens(self):
        t=threading.Thread(target=self.opens,args='')
        t.start()

    def tuichu(self, q=None):
        try:
            self.conn.close()
        except Exception as exc:
            print(exc)
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

    def to_sql_data(self,add=False,start_time='2018-01-19', end_time=str(datetime.now())):
        ''' 保存数据到合并数据库 '''
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT DATETIME,OPEN,high,low,CLOSE,vol FROM carry_investment.futures_min WHERE datetime>='{}' AND datetime<='{}'".format(
                    start_time, end_time))
            d1 = list(cur.fetchall())
            cur.execute(
                "SELECT DATETIME,OPEN,high,low,CLOSE,vol FROM carry_investment.wh_min WHERE datetime>='{}' AND datetime<='{}'".format(
                    start_time, end_time))
            d2 = cur.fetchall()
            d2 = {i[0]: i[1:] for i in d2}
            d3 = [i[0] for i in d1]
            for d in d2:
                if d not in d3:
                    d1.append((d,) + d2[d])
            d1.sort()
            if not add:
                sql = "truncate table carry_investment.handle_min"
                cur.execute(sql)
                self.conn.commit()
            for d in d1:
                try:
                    cur.execute(
                        "INSERT INTO carry_investment.handle_min(datetime,open,high,low,close,vol) values(%s,%s,%s,%s,%s,%s)",
                        (d[0], d[1], d[2], d[3], d[4], d[5]))
                except Exception as exc:
                    print(exc)
                    continue
            self.textpad.insert(1.0, '更新成功！\n')
            self.textpad.update()
        finally:
            self.conn.commit()

    def stops(self, t=None):
        self.isRun = False
        self.conn.close()

    def about(self):
        showinfo('版权信息', '凯瑞投资有限公司!')

    def help(self):
        showinfo('帮助信息', '配置文件：index_conf.conf\n默认数据库：stock_data\n默认数据表：index_min，min_last_date!')

    def main(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        filemenu = Menu(menubar)
        filemenu.add_command(label='开始', accelerator='ctrl+O', command=self.thread_opens)
        filemenu.add_command(label='停止', accelerator='Ctrl+t', command=self.stops)
        filemenu.add_command(label='退出', accelerator='Ctrl+q', command=self.tuichu)
        filemenu.add_command(label='删除', command=self.deletes)
        filemenu.add_command(label='更新数据', command=self.to_sql_data)
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
