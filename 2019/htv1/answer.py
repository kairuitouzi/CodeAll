#coding:'utf-8'
import time
import os
import win32gui, win32ui, win32con, win32api
from PIL import Image
import pytesseract
import webbrowser

def window_capture(filename):
    hwnd = 0
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    saveBitMap = win32ui.CreateBitmap()
    MoniterDev = win32api.EnumDisplayMonitors(None,None)
    #w = MoniterDev[0][2][2]
    # #h = MoniterDev[0][2][3]
    w = 380
    h = 150
    saveBitMap.CreateCompatibleBitmap(mfcDC,w,h)
    saveDC.SelectObject(saveBitMap)
    saveDC.BitBlt((0,0),(w,h),mfcDC,(20,140),win32con.SRCCOPY)
    saveBitMap.SaveBitmapFile(saveDC,filename)
start = time.time()
window_capture('haha.jpg')
text=pytesseract.image_to_string(Image.open('haha.jpg'),lang='chi_sim')
new_text =''.join(text.split())
url = 'http://www.baidu.com/s?wd=%s' % new_text
webbrowser.open(url)
end = time.time()
print(end-start)
