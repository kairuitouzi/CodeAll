import requests
import pyquery
import time
import os

"""
下载淘股吧股市大神的交易记录图片

"""

def save_img(url,nmClass,savePath):
	if not os.path.isdir(savePath):
		os.mkdir(savePath)
	for i in range(1,133):
		try:
			html = requests.get(url+str(i)).text
			html = pyquery.PyQuery(html)
			divs = html(nmClass)
			for v in divs:
				v2 = v.findall('div')[1]
				v3 = v2.findall('div')[0]
				v4 = v3.findall('img')[0]
				img_url = v4.attrib['data-original']
				img_sp = img_url.split('/')
				img_name = f'{img_sp[-4]}-{img_sp[-3]}-{img_sp[-2]}_{img_sp[-1].split(".")[0]}.jpg'
				imf = requests.get(img_url).content
				with open(savePath+img_name,'wb') as f:
					f.write(imf)
				time.sleep(0.1)
		except Exception as exc:
			print(exc)
		time.sleep(0.3)

if __name__ == '__main__':
	url = 'https://www.taoguba.com.cn/Article/175600/'
	nmClass = '.pc_p_nr.user_103830'
	savePath = 'images\\'
	save_img(url,nmClass,savePath)