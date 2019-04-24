import shelve
from pytdx.hq import TdxHq_API
from datetime import datetime
import MyUtil

class Hours:
    def __init__(self):
        try:
            self.conn = MyUtil.get_conn('stock_data')
        except Exception as exc:
            print(exc)

    def dateformat(self,a):
        return datetime(int(a[:4]),int(a[5:7]),int(a[8:10]),int(a[11:13]),int(a[14:16]))

    def write_sql_hous(self):
        api = TdxHq_API()
        conn = self.conn
        cur = conn.cursor()
        with shelve.open(r'D:\tools\Tools\demo\stock_code\code.txt') as f:
            s_code = f['code']
        with api.connect('119.147.212.81', 7709) as apis:
            sql = 'insert into moment_hours(date,open,high,low,close,amout,vol,code) values(%s,%s,%s,%s,%s,%s,%s,%s)'
            #sql = 'update moment_hours set date=%s,open=%s,high=%s,low=%s,close=%s,amout=%s,vol=%s where code=%s'
            for i in s_code:
                if i[1]=='z':
                    data = apis.get_security_bars(3, 0, i[2:], 0, 1)
                elif i[1]=='h':
                    data = apis.get_security_bars(3, 1, i[2:], 0, 1)
                else:
                    break
                try:
                    cur.execute(sql, (self.dateformat(data[0]['datetime']), data[0]['open'], data[0]['high'], data[0]['low'], data[0]['close'], data[0]['amount'], data[0]['vol'], i))
                except Exception as e:
                    print(e)
                print(i)
            conn.commit()

if __name__=='__main__':
    hours=Hours()
    try:
        hours.write_sql_hous()
    except Exception as exc:
        print(exc)
    finally:
        hours.conn.close()
