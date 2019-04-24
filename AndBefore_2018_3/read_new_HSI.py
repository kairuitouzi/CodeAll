from win32com import client as wc
import xlrd
import requests

""" 恒生指数期货各种权重系数更新 """

def read_doc(fname='FS_HSIc.doc'):
    ''' 读取 权重股 FS_HSIc.doc，返回，代码：名称，字典'''
    word = wc.Dispatch('Word.Application')
    doc = word.Documents.Open(fname)
    doc.SaveAs('FS_HSIc.txt', 4)
    doc.Close()
    word.Quit()

    with open('FS_HSIc.txt', 'r') as f:
        doc = f.readlines()
    doc1 = []
    for i in range(len(doc)):
        if '股票号码' in doc[i]:
            for j in doc[i + 1:]:
                if '合共' in j:
                    break
                doc1.append(j)
    doc = [i.split('\t') for i in doc1]
    code_name = {}
    for i in doc:
        code = 'hk'
        for n in range(5 - len(i[1])):
            code += '0'
        code += i[1]
        code_name[code] = i[3] if '太古股份公司' not in i[3] else i[3][:6]

    return code_name


def read_xls(code_name, fname='faf.xls'):
    ''' 读取流通系数与比重系数faf.xls，返回，代码：系数，字典 '''
    x = xlrd.open_workbook(fname)
    table = x.sheets()[0]
    jg = []
    for i in range(7, 658):
        try:
            tb = table.row_values(i)
            jg.append([tb[0], tb[3], tb[4]])
        except Exception as exc:
            print(exc)

    jg2 = [[i[0], i[1], i[2]] for i in jg if 'hk0' + i[0][:4] in code_name]
    jg3 = [[i[0], i[1], i[2]] for i in jg2 if 'SZ' not in i[0]]
    jg4 = {'hk0' + i[0][:4]: i[1] for i in jg3}  # 流通系数
    jg5 = {'hk0' + i[0][:4]: i[2] for i in jg3}  # 比重上限系数
    return jg4, jg5

def get_gb():
    '''
    :return:股本
    '''
    gb={'hk00005': 203.78, 'hk00011': 19.12, 'hk00023': 27.67, 'hk00388': 12.40, 'hk00939': 2404.17,
               'hk01299': 120.75, 'hk01398': 867.94, 'hk02318': 74.48, 'hk02388': 105.73, 'hk02628': 74.41,
               'hk03328': 350.12, 'hk03988': 836.22, 'hk00002': 25.26, 'hk00003': 139.88, 'hk00006': 21.34,
               'hk00836': 48.10, 'hk01038': 26.51, 'hk00004': 30.44, 'hk00012': 40.01, 'hk00016': 28.97,
               'hk00017': 101.00, 'hk00083': 64.48, 'hk00101': 44.98, 'hk00688': 109.56, 'hk00823': 8.938,
               'hk01109': 69.31, 'hk01113': 36.97, 'hk01997': 30.36, 'hk02007': 217.40, 'hk00001': 38.58,
               'hk00019': 9.05, 'hk00027': 43.14, 'hk00066': 60.08, 'hk00144': 32.78, 'hk00151': 124.62,
               'hk00175': 89.73, 'hk00267': 290.90, 'hk00288': 146.75, 'hk00386': 255.13, 'hk00700': 94.99,
               'hk00762': 305.98, 'hk00857': 210.99, 'hk00883': 446.47, 'hk00941': 204.75, 'hk00992': 120.15,
               'hk01044': 12.06, 'hk01088': 33.99, 'hk01928': 80.76, 'hk02018': 12.22, 'hk02319': 39.27,
               'hk02382': 10.97}
    #for i in gb:
    #    d=requests.get('http://quote.eastmoney.com/hk/%s.html'%i[2:]).text

    return gb

def main():
    CODE_NAME = read_doc()  # 代码：名称
    CODE_FLOW, CODE_WEIGHT = read_xls(CODE_NAME)  # 流通系数，比重系数

    # 代码：股本，亿
    CODE_EQUITY = get_gb()

    print('代码，名称：')
    print(CODE_NAME)
    print('代码：流通系数：')
    print(CODE_FLOW)
    print('代码：比重系数：')
    print(CODE_WEIGHT)
    print('代码：股本：')
    print(CODE_EQUITY)

    CODE_PRODUCT = {}
    for i in CODE_FLOW:
        try:
            CODE_PRODUCT[i] = round(CODE_EQUITY[i] * CODE_WEIGHT[i] * CODE_FLOW[i], 3)
        except Exception as exc:
            print(exc)
            print('代码：', i)
            continue
    print('CODE_PRODUCT:')
    print(CODE_PRODUCT)


if __name__ == '__main__':
    #main()
    get_gb()
