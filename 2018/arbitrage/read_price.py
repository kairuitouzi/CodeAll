import os
import h5py
import zipfile
from io import BytesIO

"""
读取恒指tick数据
计算当月与次月的价差
存放到hdf5文件
"""

def get_dt(dt):
    """ 以当月合约返回下月 """
    dt2 = int(dt)
    if dt[-2:] == '12':
        # 若为12月，则年加一，月为01
        return str(int(dt[:2]) + 1) + '01'
    else:
        # 否则直接加一
        return str(dt2 + 1)


def read_jc(path='HKDATA',hdf_path='data.hdf5'):
    """ ∫获取价差 """
    h5 = h5py.File(hdf_path, 'w')
    # 迭代目录下的所有压缩文件
    for p in os.listdir(path):
        # 打开压缩文件
        z = zipfile.ZipFile(path + os.sep + p, 'r')
        # 获取指定的CSV文件
        names = [i for i in z.namelist() if (len(i) == 16 or len(i) == 20) and ('_TR.csv' in i or '_TR_AHT.csv' in i)]
        # 迭代文件列表
        for name in names:
            res = []
            # 读取文件，为bytes类型
            data = z.read(name)
            # 获取当月合约
            _name = name[:name.index('_01_TR')][2:]
            # 获取下月合约
            _name2 = get_dt(_name)
            # 把文件转换为二维列表
            data = [i.split(',') for i in data.decode().split('\r\n')][:-1]
            data = [(i[0] + i[2], i[5] + i[6], float(i[7]), int(i[8])) for i in data if
                    i[1] == 'F' and (_name in i[2] or _name2 in i[2]) and '1' in i[9]]

            # 定义两个字典，用来存放当月与次月合约的数据
            code1 = {}
            code2 = {}

            # 迭代二维列表
            for c, d, p, v in data:
                _c = c[-4:]  # 合约，去除了代码名
                if _c == _name:  # 如果为当月合约
                    if c not in code1:  # 如果当月字典没有这个键
                        code1[c] = {d: [p * v, v]}  # 赋值一个以日期时间为键，价格与成交量为值，的字典
                    else:
                        if d not in code1[c]:   # 如果没有这个日期时间键
                            code1[c][d] = [p * v, v]  # 赋值一个 价格与成交量为值 的列表
                        else:
                            code1[c][d][0] += p * v  # 叠加 价格*成交量
                            code1[c][d][1] += v  # 叠加成交量
                elif _c == _name2:
                    if c not in code2:
                        code2[c] = {d: [p * v, v]}
                    else:
                        if d not in code2[c]:
                            code2[c][d] = [p * v, v]
                        else:
                            code2[c][d][0] += p * v
                            code2[c][d][1] += v

            # 迭代当月数据字典
            for i in code1:
                k1 = i[:-4] + get_dt(i[-4:])  # 获取下月合约名
                for j in code1[i]:
                    # 若下月数据字典存在与当前合约字典对应的精确到秒的数据
                    if k1 in code2 and j in code2[k1]:
                        # 计算价差
                        price1 = round(code1[i][j][0] / code1[i][j][1], 3)
                        price2 = round(code2[k1][j][0] / code2[k1][j][1], 3)
                        # （当月合约名，次月合约名，日期时间，价差，当月秒均价，次月秒均价）
                        res.append((i.encode(), k1.encode(), j.encode(), str(round(price1 - price2, 3)).encode(),
                                    str(price1).encode(), str(price2).encode()))
            # 以日期时间升序排序
            res.sort(key=lambda x: x[2])

            # 存入HDF5文件
            h5['TR/'+name[:-4]] = res

            print(name)
    h5.close()


def get_hdf(name='HSI'):
    """ 获取hdf5的数据
        name: HSI, HHI, MHI """
    # 读取hdf5文件
    data = h5py.File('data.hdf5','r')
    # 获取所有的键
    k = [i for i in data['TR'].keys()]
    res = []  # 用来存放所有结果
    # 迭代获取所有的值
    for i in k:
        d = data[f'TR/{i}']
        d = [[i[0].decode(),i[1].decode(),i[2].decode(),float(i[3]),float(i[4]),float(i[5])] for i in d if i[0].decode()[:3] == name]
        res += d
    return res



if __name__ == '__main__':
    read_jc()