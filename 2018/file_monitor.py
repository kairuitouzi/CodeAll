import os
import win32file
import datetime
import win32con
import threading

import wh_dat

def main():
    """ 
    监听某目录的文件，如果文件有更新，则调用函数读取已经更新的
    文件，被调用的函数wh_dat.main会把更新的数据存储到数据库 
    """
    ACTIONS = {
        1: "Created",
        2: "Deleted",
        3: "Updated",
        4: "Renamed from something",
        5: "Renamed to something"
    }

    FILE_LIST_DIRECTORY = win32con.GENERIC_READ | win32con.GENERIC_WRITE
    path_to_watch = r'C:\wh6模拟版\Data'  # 要监听文件的路径
    hDir = win32file.CreateFile(
        path_to_watch,
        FILE_LIST_DIRECTORY,
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
        None,
        win32con.OPEN_EXISTING,
        win32con.FILE_FLAG_BACKUP_SEMANTICS,
        None
    )

    while 1:
        results = win32file.ReadDirectoryChangesW(
            hDir,  # handle(句柄)：要监视的目录的句柄。这个目录必须用 FILE_LIST_DIRECTORY 访问权限打开。 
            1024,  # size(大小): 为结果分配的缓冲区大小。
            True,  # bWatchSubtree: 指定 ReadDirectoryChangesW 函数是否监视目录或目录树。
            win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
            win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
            win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
            win32con.FILE_NOTIFY_CHANGE_SIZE |
            win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
            win32con.FILE_NOTIFY_CHANGE_SECURITY,
            None,
            None)
        for action, file in results:
            full_filename = os.path.join(path_to_watch, file)
            status = ACTIONS.get(action, "Unknown")
            print(full_filename, status)
            if status == "Updated" and '.dat' in full_filename:
                insert_size = whcj.main(full_filename)
                if insert_size is not None:
                    print(str(datetime.datetime.now())[:19], ' Update {} data to the MySQL database.'.format(insert_size))
                else:
                    print(str(datetime.datetime.now())[:19], '字典里没有此文件！')

if __name__ == '__main__':
    # 初始化文华财经类
    whcj = wh_dat.WHCJ()
    t1=threading.Thread(target=main)
    t2=threading.Thread(target=whcj.runs)
    t1.start()
    t2.start()