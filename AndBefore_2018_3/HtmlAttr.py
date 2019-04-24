from pyquery import PyQuery as pq
import re,time

def read_input():
    with open('test1.html','rb') as f:
             doc=f.read()
    d=pq(doc)
    s=d('input')
    for i in s.items():
        if i.attr('name') and i.attr('value'):
            print(i.attr('name'),'  ',i.attr('value'))


def read_js_var():
    with open('hsi.html','rb') as f:
        doc=f.read().decode()
    doc=doc.replace('\n','').replace('\t','').replace('\r','')
    results=[]
    try:
        a=(re.findall('prodNameF=(.*?);',doc))
        b=re.findall('prodMonthF=(.*?);',doc)
        a=exec('results.append(%s)'%a[0])
        b=exec('results.append(%s)'%b[0])
    except Exception as exc:
        print(exc)
    return results

if __name__=='__main__':
    
    print(read_js_var())

