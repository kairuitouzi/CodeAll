import re
import os
import time
import chardet
import requests
from urllib import parse

"""
下载整个网站的 js、css、img、html 文件
"""


def write_file(names, files, char):
    """ 写入到文件 """
    name = names.split('/')[-1]
    path = ''
    if '.html' in name:
        if '?' in name:
            name = name.split('?')
            name2 = name[0].split('.')
            path = name2[0] + '_' + name[1] + '.' + name2[1]
        else:
            path = name
    elif '.js' in name:
        path = 'js\\' + name
    elif '.css' in name:
        path = 'css\\' + name
    else:
        path = 'images\\' + name
    if char == 'bytes':
        with open(path, 'wb') as f:
            f.write(files)
    else:
        with open(path, 'w', encoding=char) as f:
            f.write(files)


def down_html(url, h=True):
    """ 下载文件 """
    html = requests.get(url).content
    if not h:
        return html, 'bytes'
    char = chardet.detect(html)
    html = html.decode(char['encoding'])  # 转换编码
    return html, char['encoding']


def get_index_a(index_url, index=False):
    """ 获取主页面的所有a标签，js,css,图片 """
    alls = []
    # is_downs = []
    if '.html' in index_url or index:
        html, char = down_html(index_url)
    else:
        html, char = down_html(index_url, h=False)
        url = index_url.split('/')[-1]
        write_file(url, html, char)
        return alls
    # 抽取 a 标签
    comp = re.compile(r'<a.*?href="(.*?)"')
    a = comp.findall(html)
    a = set(a)
    index_url2 = parse.urlsplit(index_url)[:2]
    index_url2 = index_url2[0] + '://' + index_url2[1] + '/'
    a = [index_url2 + i for i in a if i and i not in (' ', '#', '/') and 'javascript:' not in i.lower() and i[0] == '/']
    alls.extend(a)
    bold = re.compile(r'<a(?P<b1>.*?)href=".*/(?P<b2>.*?).html')
    html = bold.sub(r'<a\g<b1>href="\g<b2>.html', html)

    # 把所有页面的 a 标签的 href 改变成能在本地访问的
    bold = re.compile(r'<a(?P<b1>.*)href="(?P<b2>.*).html\?tid=(?P<b3>.*)"')
    html = bold.sub(r'<a\g<b1>href="\g<b2>_tid=\g<b3>.html"', html)

    # 抽取 css 链接
    css = re.findall(r'<link.*?href="(.*?)"', html)
    css = set(css)
    css = [index_url2 + i for i in css if '.css' in i]
    alls.extend(css)
    bold = re.compile(r'<link(?P<b1>.*?)href=".*/(?P<b2>.*?).css')
    html = bold.sub(r'<link\g<b1>href="css/\g<b2>.css', html)

    # 抽取 js 链接
    js = re.findall(r'<script .*?src="(.*?)"', html)
    js = set(js)
    js = [index_url2 + i for i in js if '.js' in i]
    alls.extend(js)
    bold = re.compile(r'<script(?P<b1>.*?)src=".*/(?P<b2>.*?).js')
    html = bold.sub(r'<script\g<b1>src="js/\g<b2>.js', html)

    # 抽取 img 链接
    img = re.findall(r'<img .*?src="(.*?)"', html)
    img = set(img)
    img = [index_url2 + i for i in img]
    alls.extend(img)
    bold = re.compile(r'<img(?P<b1>.*?)src=".*/(?P<b2>.*?)"')
    html = bold.sub(r'<img\g<b1>src="images/\g<b2>"', html)

    # 如果是首页就默认为 index.html
    url = 'index.html' if index else index_url.split('/')[-1]
    write_file(url, html, char)
    return alls  # ,is_downs


def main(index_url):
    # 创建文件夹
    for i in ('js', 'css', 'images'):
        if not os.path.isdir(i):
            os.mkdir(i)
    alls, is_downs = [], []
    alls2 = get_index_a(index_url, index=True)
    is_downs.append(index_url)
    alls.extend([i for i in alls2 if i not in is_downs])
    while 1:
        if not alls:
            break
        url = alls.pop()
        if url in is_downs:
            print(f'已经下载：{url}')
            continue
        try:
            alls2 = get_index_a(url)
            print(f'文件成功下载：{url}')
        except Exception as exc:
            print(f'错误：{url} ')
            print(exc)
        is_downs.append(url)
        alls.extend([i for i in alls2 if i not in is_downs])
        time.sleep(0.5)


if __name__ == '__main__':
    # 网站主页
    index_url = 'http://192.168.2.204/'
    main(index_url)
