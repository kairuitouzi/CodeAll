import time
import os
from datetime import datetime


class Hsimin:
    def __init__(self, min_input=None, dirs=None):
        if min_input is None:
            min_input='HSIc1'  
        self.min_input=min_input      
        if dirs is None:
            dirs='D:\\同花顺软件\\同花顺港股版\\history\\hz\\min'
        self.dirs = dirs + '\\' + min_input + '.min'
        self.file_object = open(self.dirs, 'rb')        
        # self.min_input='D:\\tools\\Tools\\日期\\2017-12-18\\min'

    def read_zhishu_min(self):
        file_object = self.file_object
        file_object.seek(0)
        try:
            txt = file_object.read()
            nrd0 = txt[6]
            nrd1 = txt[7] * 256
            nrd2 = txt[8] * 256 * 256
            nrd3 = txt[9] * 256 * 256 * 256
            nrd0 = nrd0 + nrd1 + nrd2 + nrd3
            rtsp = txt[10] + txt[11] * 256
            # print("记录开始位置=" , rtsp)
            terd = txt[12] + txt[13] * 256
            # print("每记录的长度=" , terd)
            j = 1
            ivx = 1 + rtsp + terd * (
                nrd0 - 1)  # 最后的一条记录
            zhongji = dict()
            # 时间处理
            ivy0 = txt[ivx - 1]
            ivy1 = txt[ivx]
            ivy1 = ivy1 * 256
            ivy2 = txt[ivx + 1]
            ivy2 = ivy2 * 256 * 256
            ivy3 = txt[ivx + 2]
            ivy3 = ivy3 * 256 * 256 * 256
            ivy0 = ivy0 + ivy1 + ivy2 + ivy3
            Times = list()
            Times.append(int(ivy0 / 1048576) + 1900)  # yyyy-
            Times.append(int((ivy0 % 1048576) / 65536))  # yyyy-mm-
            Times.append(int((ivy0 % 65536) / 2048))  # yyyy-mm-dd
            Times.append(int((ivy0 % 2048) / 64))  # yyyy-mm-dd-hh:
            Times.append(ivy0 % 64)  # yyyy-mm-dd-hh-mm

            zhongji['time'] = datetime(Times[0], Times[1], Times[2], Times[3], Times[4])
            # 开盘价
            ivy0 = txt[ivx + 3]
            ivy1 = txt[ivx + 4]
            ivy1 = ivy1 * 256
            ivy2 = txt[ivx + 5]
            ivy2 = ivy2 * 256 * 256
            ivy3 = txt[ivx + 6]
            ivy3 = ivy3 % 16
            ivy3 = ivy3 * 256 * 256 * 256
            ivy0 = ivy0 + ivy1 + ivy2 + ivy3
            tpsg = ""
            tpsg = tpsg + str(int(ivy0 / 1000))  # 整数位
            tpsg = tpsg + "."
            tpsg = tpsg + str(int(ivy0 % 1000))  # 小数位
            zhongji['open'] = tpsg
            # 最高价
            ivy0 = txt[ivx + 7]
            ivy1 = txt[ivx + 8]
            ivy1 = ivy1 * 256
            ivy2 = txt[ivx + 9]
            ivy2 = ivy2 * 256 * 256
            ivy3 = txt[ivx + 10]
            ivy3 = ivy3 % 16
            ivy3 = ivy3 * 256 * 256 * 256
            ivy0 = ivy0 + ivy1 + ivy2 + ivy3
            tpsg = ""
            tpsg = tpsg + str(int(ivy0 / 1000))  # 整数位
            tpsg = tpsg + "."
            tpsg = tpsg + str(int(ivy0 % 1000))  # 小数位
            zhongji['high'] = tpsg
            # 最低价
            ivy0 = txt[ivx + 11]
            ivy1 = txt[ivx + 12]
            ivy1 = ivy1 * 256
            ivy2 = txt[ivx + 13]
            ivy2 = ivy2 * 256 * 256
            ivy3 = txt[ivx + 14]
            ivy3 = ivy3 % 16  # 防溢出处理，同时也将最高位的XY中的X修改为0
            ivy3 = ivy3 * 256 * 256 * 256
            ivy0 = ivy0 + ivy1 + ivy2 + ivy3
            tpsg = ""
            tpsg = tpsg + str(int(ivy0 / 1000))  # 整数位
            tpsg = tpsg + "."
            tpsg = tpsg + str(int(ivy0 % 1000))  # 小数位
            zhongji['low'] = tpsg
            # 收盘价
            ivy0 = txt[ivx + 15]
            ivy1 = txt[ivx + 16]
            ivy1 = ivy1 * 256
            ivy2 = txt[ivx + 17]
            ivy2 = ivy2 * 256 * 256
            ivy3 = txt[ivx + 18]
            ivy3 = ivy3 % 16
            ivy3 = ivy3 * 256 * 256 * 256
            ivy0 = ivy0 + ivy1 + ivy2 + ivy3
            tpsg = ""
            tpsg = tpsg + str(int(ivy0 / 1000))  # 整数位
            tpsg = tpsg + "."
            tpsg = tpsg + str(int(ivy0 % 1000))  # 小数位
            zhongji['close'] = tpsg
            # 成交额
            ivy0 = txt[ivx + 19]
            ivy1 = txt[ivx + 20]
            ivy1 = ivy1 * 256
            ivy2 = txt[ivx + 21]
            ivy2 = ivy2 * 256 * 256
            ivy3 = txt[ivx + 22]
            ivy3 = ivy3 % 16  # 防溢出处理，同时也将最高位的XY中的X修改为0
            ivy3 = ivy3 * 256 * 256 * 256
            ivy0 = ivy0 + ivy1 + ivy2 + ivy3
            ivy0 = ivy0 * 10
            zhongji['amount'] = ivy0
            # 成交量股
            ivy0 = txt[ivx + 23]
            ivy1 = txt[ivx + 24]
            ivy1 = ivy1 * 256
            ivy2 = txt[ivx + 25]
            ivy2 = ivy2 * 256 * 256
            ivy3 = txt[ivx + 26]
            ivy3 = ivy3 % 16  # 防溢出处理，同时也将最高位的XY中的X修改为0
            ivy3 = ivy3 * 256 * 256 * 256
            ivy0 = ivy0 + ivy1 + ivy2 + ivy3

            zhongji['vol'] = ivy0
            zhongji['prod_code']=self.min_input            
            return zhongji

        except Exception as exc:
            print(exc)
            return

    def close_file(self):
        self.file_object.close()


if __name__ == '__main__':
    #par = 'D:\\tools\\Tools\\日期\\2017-12-18\\min'
    # print('时间\t', '开盘\t', '最高\t', '最低\t', '收盘\t', '成交额\t', '成交量\t')

    hsi = Hsimin(min_input='HSIc2',dirs=None)                  #初始化类并赋值

    result = hsi.read_zhishu_min()
    print(result)

    hsi.close_file()  #关闭文件
