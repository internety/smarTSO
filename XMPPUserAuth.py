#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  7 16:58:52 2016

@author: s
"""
"""
def sample():
    import cStringIO as StringIO
    import xmltodict
    plik= '/home/s/s3tt-sorted/smarTSO/_P/xmpp-response-dump'
    dane = StringIO.StringIO(open(plik, 'r').read()).read()
    sample = xmltodict.parse(dane)
    return sample
sam=sample()
"""

from mitmproxy.script import concurrent
from mitmproxy.models import decoded
from threading2 import Thread
from re2 import search
from pymysql import connect
from os import path
from sys import stdout
from time import time
import logging, xmltodict
global log

cfg= { 'mysql_user' : 'smartso',
       'mysql_pass' : '6yMODY)gxpGp',
       'mysql_db'   : 'smartso',
       'mysql_host' : '127.0.0.1',
       'unique_pattern' : "596bc25a-00ec-46c6-806f-73855d5c2325",  }

if '__file__' in locals().keys():
    BASEDIR= path.abspath(path.dirname(__file__))
else:
    BASEDIR='/home/s/smarTSO/'
    print ("'__file__' not defined, assuming hardcoded BASEDIR: %s"%BASEDIR)

    
def getloggerinstance():
    """ https://docs.python.org/2/howto/logging-cookbook.html """
    log   =logging.getLogger()
    hdlr = logging.FileHandler(path.join(BASEDIR,'SzpieGwiazdor.log'))
    formatter = logging.Formatter('%(asctime)s %(filename)s %(lineno)s %(funcName)15s() %(levelname)s : %(message)s')
    hdlr.setFormatter(formatter)
    #log.addHandler(hdlr)
    ch = logging.StreamHandler(stdout)
    ch.setFormatter(formatter)
    log.addHandler(ch) 
    log.setLevel(logging.DEBUG)
    FORMAT="[%(msecs)s;%(filename)s:%(lineno)s:%(funcName)15s()] %(message)s"
    logging.basicConfig(format=FORMAT)
    return log
log=getloggerinstance()

db = connect( cfg['mysql_host'], 
              cfg['mysql_user'],
              cfg['mysql_pass'],
              cfg['mysql_db']    )
db.autocommit(True)
db.ping(reconnect=True)

def xmpparseone(single):
    if single.get( 'body' ).startswith( cfg['unique_pattern'] ):
        ts      = time().__int__()
        xid     = single['bbmsg']['@playerid']
        xname   = single['bbmsg']['@playername']
        xtag    = '' if single['bbmsg']['@playertag']=='null' else single['bbmsg']['@playertag']
        xkey    = single['body'][ len(cfg['unique_pattern']): ]
        xserver = single['@to'].split('@')[1].split('/')[0]
        cur = db.cursor()
        sql_try = """SELECT * from auth where x_playername=%s and x_playerid=%s and x_server=%s"""
        cur.execute(sql_try, (xname, xid, xserver))
        if cur.rowcount > 0:
            print 'gracz istnieje'
            return False
        else:
            print 'nowy gracz'
        sql= """INSERT INTO auth 
             ( x_playername, x_playerid, x_playertag, x_server, x_key, x_ts )
             VALUES (%s,%s,%s,%s,%s,%s)"""
        datas = (xname, xid, xtag, xserver, xkey, ts)
        cur.execute(sql, datas)
        db.commit()
        log.info("player %s / %s added with key %s on server %s"%(xname, xid, xkey, xserver))
        print ('cur.execute(ts, xid, xname, xtag, xkey, xserver)',ts, xid, xname, xtag, xkey, xserver)
    
def xmpparser(msg):
    m = xmltodict.parse(msg)
    if not 'message' in m['body'].keys():
        return False
    if type(m['body']['message']).__name__ == 'list':
        for single in m['body']['message']:
            xmpparseone(single)
    else:
            xmpparseone(m['body']['message'])
    


@concurrent
def response(context, flow): 
    if "text/xml" in flow.request.headers.get('Content-Type',"_") and \
       flow.request.path == "/http-bind/" and \
       "Jetty" in flow.response.headers.get('Server',"_") and \
       flow.request.host.endswith('.thesettlersonline.pl'):
       with decoded(flow.response):
           res = flow.response.content
           if search( cfg['unique_pattern'], res):
               try:
                   t= Thread(target=xmpparser, args=(flow.response.content,))
                   t.setDaemon(True) 
                   t.start()
               except (KeyboardInterrupt, SystemExit):
                   log.info('caught either KeyboardInterrupt or SystemExit, quitting threads')
                   t.__stop()
                   import thread
                   thread.interrupt_main()

                   