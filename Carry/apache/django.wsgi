import os,sys

#os.environ['DJANGO_SETTINGS_MODULE']='Carry.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Carry.settings")

sys.path.append('C:/Users/Administrator/Desktop/djpy/Carry')

import django.core.handlers.wsgi as dchw
application=dchw.WSGIHandler()


