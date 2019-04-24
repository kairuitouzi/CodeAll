import itchat, time, re, requests, os, json
from itchat.content import *
import urllib.request as rq
from MyUtil import MyUtil
from pytdx.hq import TdxHq_API

api = TdxHq_API()
myutil = MyUtil()
myfmt = {'t': ['T', '分时', '时', '时K', 'FS'],
         'd': ['D', '日', '日K', 'RX'],
         'w': ['W', '周', 'ZX', '周K'],
         'm': ['M', '月', 'YX', '月K']}


def tuling(info):
    appkey = "14283e062e694e7398453680634cbcfc"
    url = "http://www.tuling123.com/openapi/api?key=%s&info=%s" % (appkey, info)
    req = requests.get(url)
    content = req.text
    data = json.loads(content)
    answer = data['text']
    return answer


def getCodePicture(msg, param, s):
    rq_code, picture, types, isPicture = None, None, None, True
    if s and s in myfmt['t']:  # 分时K线
        types = 'min'
    elif s and s in myfmt['d']:  # 日K线
        types = 'daily'
    elif s and s in myfmt['w']:  # 周K线
        types = 'weekly'
    elif s and s in myfmt['m']:  # 月K线
        types = 'monthly'
    else:  # 返回股票文本信息
        isPicture = False
        getText(msg, param)
    if len(param) <= 2 and os.path.isfile('myfile\\%s.txt' % msg['FromUserName']):
        with open('myfile\\%s.txt' % msg['FromUserName']) as f:
            rq_code = f.readlines()[-1].strip('\n').split()
    else:
        rq_code = myutil.getCode(param.strip()[1:])
    if rq_code and types:
        picture = rq.urlopen('http://image.sinajs.cn/newchart/%s/n/%s.gif' % (types, rq_code[0])).read()
    return rq_code, picture, isPicture


def getText(msg, news):
    rq_code = myutil.getCode(news[1:])
    if rq_code:
        '''try:
            with api.connect('119.147.212.81', 7709) as apis:
                if rq_code[0][1]=='z':
                    data = apis.get_security_bars(9, 0, rq_code[0][2:], 0, 1)
                elif rq_code[0][1]=='h':
                    data = apis.get_security_bars(9, 1, rq_code[0][2:], 0, 1)
        except AttributeError:'''
        d = requests.get('http://hq.sinajs.cn/list=%s' % rq_code[0]).text
        d1 = d.split(',')
        try:
            extent = (float(d1[3]) - float(d1[2])) / float(d1[2]) * 100
            extent = 0 if (extent >= 11 or -extent >= 11) else extent
        except:
            extent = 0
        with open('myfile\\%s.txt' % msg['FromUserName'], 'a') as f:
            f.write(rq_code[0] + ' ' + rq_code[1] + '\n')
        if ':' in d1[-2]:
            dd = d1[-2].split(':')
            if int(dd[0]) >= 15 and int(dd[1]) >= 1:
                d1[-2] = '15:00:00'
        itchat.send('股票名称：%s\n股票代码：%s\n当前价格：%s\n昨日收盘价：%s\n开盘价：%s\n最高价：%s\n最低价：%s\n涨跌幅度：%.3f%s\n时间：%s'
                    % (rq_code[1], rq_code[0], d1[3], d1[2], d1[1], d1[4], d1[5], extent, '%', d1[-2]),
                    toUserName=msg['FromUserName'])


def mysends(msg):
    a = msg['Content']
    news, rq_code, isPicture = None, None, True  # 请求信息，请求代码，是否返回图片
    try:
        news = a[a.index('\u2005') + 1:].upper().strip()
    except:
        news = a.upper().strip()
    print(news)
    if news and (news[0] == '%' or news[0] == '％'):
        news = news.split()
        if len(news[0]) >= 7 and len(re.findall('\d', news[0])) >= 5:
            if len(news) == 1:
                param, s = news[0][:7], news[0][7:]
                rq_code, picture, isPicture = getCodePicture(msg, param, s)
            elif len(news) >= 2:
                param, s = news[0], news[1]
                rq_code, picture, isPicture = getCodePicture(msg, param, s)
            else:  # 返回股票文本信息
                isPicture = False
                getText(msg, news[0])
        elif len(news) == 1 and len(news[0]) > 5:
            param, s = news[0][:5], news[0][5:]
            rq_code, picture, isPicture = getCodePicture(msg, param, s)
        elif len(news) >= 2:
            param, s = news[0], news[1]
            rq_code, picture, isPicture = getCodePicture(msg, param, s)
        elif len(news[0]) <= 2:
            param, s = news[0].strip(), news[0].strip()[1:]
            rq_code, picture, isPicture = getCodePicture(msg, param, s)

        else:  # 返回股票文本信息
            isPicture = False
            getText(msg, news[0])

        if isPicture and rq_code:
            with open('myfile\\%s.png' % rq_code[0], 'wb') as f:
                f.write(picture)
            itchat.send_image('myfile\\%s.png' % rq_code[0], toUserName=msg['FromUserName'])
    else:
        if news in ['START', 'STOP']:
            with open('myfile\\flag.txt', 'w') as f:
                f.write(news)
        if os.path.isfile('myfile\\flag.txt'):
            with open('myfile\\flag.txt', 'r') as f:
                flag = f.read()
            if flag == 'START':
                res_info = tuling(msg['Content'])
                itchat.send(res_info, toUserName=msg['FromUserName'])


@itchat.msg_register([TEXT, PICTURE, MAP, CARD, NOTE, SHARING, RECORDING, ATTACHMENT, VIDEO])
def text_reply(msg):
    mysends(msg)


@itchat.msg_register(TEXT, isGroupChat=True)
def group_text_reply(msg):
    if msg.isAt:
        mysends(msg)


def login():
    if not os.path.isdir('myfile'):
        os.mkdir('myfile')


def exits():
    for i in os.listdir('myfile'):
        os.remove('myfile\\' + i)
    os.removedirs('myfile')


if __name__ == '__main__':
    itchat.auto_login(hotReload=True, loginCallback=login, exitCallback=None)  # 登陆，并存储登陆状态
    itchat.run()
    for i in os.listdir('myfile'):
        os.remove('myfile\\' + i)
    os.removedirs('myfile')
