"""
Python FTP 操作

from ftplib import FTP      # 加载ftp模块
ftp = FTP()                 # 获取FTP对象
ftp.set_debuglevel(2)       # 打开调试级别2，显示详细信息
ftp.connect('IP', PORT) # 连接ftp，server和端口
ftp.login('user', 'password')  # 登录用户
print(ftp.getwelcome())     # 打印欢迎信息
ftp.cmd('xxx/xxx')          # 进入远程目录
bufsize = 1024              # 设置缓存区大小
filename='filename.txt'     # 需要下载的文件
file_handle=open(filename, 'wb').write   # 以写的模式在本地打开文件
file.retrbinaly('RETR filename.txt', file_handle,bufsize)  # 接收服务器上文件并写入本地文件
ftp.set_debuglevel(0)       # 关闭调试模式
ftp.quit                    # 退出ftp


ftp相关的命令操作
ftp.cwd(pathname)           # 设置FTP当前操作的路径
ftp.dir()                   # 显示目录下所有目录的信息
ftp.nlst()                  # 获取目录下的文件
ftp.mkd(pathname)           # 新建远程目录
ftp.rmd(dirname)            # 删除远程目录
ftp.pwd()                   # 返回当前所在位置
ftp.delete(filename)        # 删除远程文件
ftp.rename(fromname, toname)    #将fromname改为toname
ftp.storbinaly('STOR filename.txt',file_handel,bufsize)  # 上传目标文件
ftp.retrbinary('RETR filename.txt',file_handel,bufsize)  # 下载FTP文件
"""

import os
from ftplib import FTP



class FTPClient(FTP):
    """ FTP 客户端 """

    def ftplogin(self, host, port, username, password):
        """ 登录 """
        self.connect(host, port)
        self.login(username, password)


    def downloadfile(self, remotepath, localpath=None):
        """ 下载文件 """
        bufsize = 1024
        if localpath is None:
            localpath = os.path.basename(remotepath)
        fp = open(localpath, 'wb')
        self.retrbinary('RETR ' + remotepath, fp.write, bufsize)
        self.set_debuglevel(0)
        fp.close()
        print(f'文件 {remotepath} 下载成功！')

    def uploadfile(self, localpath, remotepath=None):
        """ 上传文件 """
        bufsize = 1024
        if remotepath is None:
            remotepath = os.path.basename(localpath)
        fp = open(localpath, 'rb')
        self.storbinary('STOR ' + remotepath, fp, bufsize)
        self.set_debuglevel(0)
        fp.close()
        print(f'文件 {localpath} 上传成功！')

    def uploadfolder(self, localpath):
        """ 上传文件夹 """
        bufsize = 1024
        _fold = os.path.basename(localpath)
        try:
            self.mkd(_fold)
        except Exception as exc:
            if 'exists' in str(exc):
                cz = input(f'目录 {_fold} 已经存在，是否覆盖其所有文件(Y/N)：')
                if cz != 'Y':
                    return
        self.cwd(_fold)
        next_fold = []
        for i in os.listdir(localpath):
            _f = os.path.join(localpath,i)
            if os.path.isfile(_f):
                fp = open(_f, 'rb')
                self.storbinary('STOR ' + i, fp, bufsize)
                self.set_debuglevel(0)
                fp.close()
            elif os.path.isdir(_f):
                next_fold.append((_fold,_f))

        for j,i in next_fold:
            v = self.pwd().split('/')
            if j != v[-1]:
                self.cwd('../')
            self.uploadfolder(i)

        print(f'文件夹 {localpath} 上传成功！')


if __name__ == '__main__':
    host = '137.59.148.114'  # IP
    port = 21             # 端口
    user = input('用户名:')           # 用户名
    password = input('密码:')     # 密码
    ftp = FTPClient()
    ftp.ftplogin(host, port, user, password)  # 登录
    # ftp.downloadfile('c.txt')  # 下载文件
    ftp.cwd('public_html')
    ftp.uploadfolder('qh')  # 上传文件夹 qh
    ftp.quit()