import re
import h5py
from xpinyin import Pinyin
import numpy as np
import MyUtil

def read_stock_code(dirs):
    p=Pinyin()
    for mydir in dirs:
        with open(mydir) as f:
            data=f.readlines()
        ix=0
        while ix<len(data):
            s=data[ix].strip('\n').split('=')
            if not s[0]:
                ix+=1
                continue
            if len(s)<2:
                ix+=2
                continue
            
            code=s[0]
            cnames=s[1].split('|')
            if len(cnames)>1:
                chineseName=cnames[0].replace(' ','')
                initial=''
                for i in p.get_initials(cnames[0].replace(' ','')).replace('-',''):
                    cod=ord(i)
                    if 65312<cod<65339:
                        i=chr(cod-65248)
                    initial=initial+i
                spareCode=cnames[1][:-2]
            else:
                chineseName=cnames[0].replace(' ','')
                initial=''
                for i in p.get_initials(cnames[0].replace(' ','')).replace('-',''):
                    cod=ord(i)
                    if 65312<cod<65339:
                        i=chr(cod-65248)
                    initial=initial+i
                spareCode=None
            
            bazaar=None
            if mydir[-9:-7]=='16':
                bazaar='sh'
            elif mydir[-9:-7]=='32':
                bazaar='sz'
            elif '176' in mydir:
                bazaar='hk'
            yield [code,chineseName,initial,spareCode,bazaar]
            ix+=1
        print(mydir)

def main():
    dirs=[r'D:\同花顺软件\同花顺\stockname\stockname_16_0.base',
          r'D:\同花顺软件\同花顺\stockname\stockname_32_0.base',
          r'D:\同花顺软件\同花顺\stockname\stockname_176_0.base']
    
    try:
        conn = MyUtil.get_conn('stock_data')
        cur = conn.cursor()
        cur.execute('delete from stock_code')
        conn.commit()
    except Exception as exc:
        print(exc)
    for res in read_stock_code(dirs):
        try:
            cur.execute('INSERT INTO stock_code(code,chineseName,initial,spareCode,bazaar) VALUES(%s,%s,%s,%s,%s)',(res[0],res[1],res[2],res[3],res[4]))
        except:
            try:
                cur.execute('UPDATE stock_code SET chineseName="%s",initial="%s",spareCode="%s" WHERE code="%s" AND bazaar="%s"'%(res[1],res[2],res[3],res[0],res[4]))
            except Exception as exc:
                print(exc)
    conn.commit()
    conn.close()



if __name__=='__main__':
    main()
