#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
  ver 2016.09.13.2248  /  @author: s
=============================================================================
zapamiętuje zawartości gwiazdek graczy parsując gałęzie "playersOnMap".
wyniki lądują w tabeli 'gwiazda'





def sample():
    import cStringIO as StringIO
    from amfast import decoder
    trade= '/home/s/s3tt-sorted/smarTSO/amf-1001-visitfriend'
    dane = StringIO.StringIO(open(trade, 'r').read()).read()
    mess = decoder.decode_packet(dane)
    sample = mess.messages[0].body.body['data']['data']
    return sample
sam=sample()
                                                                         #####
                                                                         * ##
                                                                         ## *
________________________________________________________________________#####
WYMAGANIA: 
   amfast, mitmproxy, re2, pymysql, threading2, pysqlite, attrdict, lru-dict
"""


from mitmproxy.script import concurrent
from mitmproxy.models import decoded
from amfast import decoder as amfdec
from nested_lookup import nested_lookup
from threading2 import Thread
from re2 import search
from attrdict import AttrDict
from pymysql import connect
from os import path
from sys import stdout
from expiringdict import ExpiringDict
from time import time
from collections import Counter
import logging
global log, BASEDIR


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

   
class SGD(object):
    """ SzpieGwiazdor """    

    def __init__(self, **kwargs):
        cfg_defaults= { 'mysql_user' : None,
                        'mysql_pass' : None,
                        'mysql_db' : None,
                        'mysql_host' : None }
        self.c = AttrDict()
        for k in cfg_defaults.keys():
            if kwargs.has_key(k):
                self.c[k]=kwargs[k]
            elif cfg_defaults[k]:
                self.c[k]=cfg_defaults[k]
                log.info("przyjęto domyślne ustawienie dla %s"%k)
            else:
                raise Exception("ustawienia niekompletne, brak %s"%k)
        self.c.db = connect(self.c.mysql_host, 
                            self.c.mysql_user, 
                            self.c.mysql_pass,
                            self.c.mysql_db )
        self.c.db.autocommit(False)
        self.c.cur = self.c.db.cursor()
        self.recent_act = ExpiringDict(256,300)


    def _amf_raw_response_parser(self, rawamf):
        """ przetwarza surową odpowiedź AMF (iteruje po zawartych wiadomościach
            (message), wybiera tą o numerze 1061 (trade update), zwraca body pierwszej
            pasującej lub None) """
        decresp = amfdec.decode_packet( rawamf )
        for m in decresp.messages:
            if m.body.body.has_key('type') and int(m.body.body['type'])== 1001 \
            and m.body.body.has_key('data') and m.body.body['data'].has_key('data')\
            and isinstance(m.body.body['data']['data'], dict):
                    if m.body.body['data']['errorCode']==0:
                        return m.body.body
                    else:
                        errcode = m.body.body['data']['errorCode']
                        log.error('amf error, code:%s') %errcode
        return None
            
          
    def _pom_remove_if_exists(self, pID, pN):
        sql = """DELETE FROM gwiazda WHERE playerID = %d AND playerName = '%s';"""%(pID, pN)
        self.c.cur.execute(sql)
        log.info('gracz/ID %s/%d: usunięto %d pozycji'%(pN, pID, self.c.cur.rowcount))
        self.c.db.commit()
        
        
    def _pom_generate_objects(self, pID, pN, buffsvector):
        return [self.StarItem( pID, pN, **pd ) for pd in buffsvector]
        
    def _pom_insert_star_list(self, pID, pN, star_menu):
        sqllines = [b._sql_ins_data() for b in star_menu]
        query= """  INSERT IGNORE INTO gwiazda
                  ( playerID,          playerName,            amount,
                    buffName_string,   resourceName_string,   kiedyZlapanoTS  )  
                    VALUES ( %s,%s,%s,%s,%s,%s ) """ 
        self.c.cur.executemany(query, sqllines)
        log.info('gracz/ID %s/%d: dodano %d pozycji'%(pN, pID, self.c.cur.rowcount))
        self.c.db.commit()

    def _incoming_traffic_handler(self, response):
        """ logika postępowania z przechwyconym ruchem (1001 response) """
        resp_1001= self._amf_raw_response_parser(response)
        pom      = nested_lookup('playersOnMap', resp_1001)
 
        for pd in pom[0]:
            bv = pd.get('availableBuffs_vector')
            if bv:
                pID = pd['userID']
                pN  = pd['username_string']
                recent_key = ":".join([str(pID),pN])
                ittl= self.recent_act.ttl( recent_key )
                if ittl:
                    log.info('gracz/ID %s/%d: ignorowanie jeszcze %d sekund'%(pN, pID, ittl))
                    return None
                else:
                    adventure_cntr = dict(Counter(b['resourceName_string'] for b in [a for a in bv if a['buffName_string'] == "Adventure"]))
                    adventure_list = [self.StarItem(pID, pN, "Adventure", i[0], i[1]) for i in adventure_cntr.iteritems()]
                    otheritms_list = [self.StarItem(pID, pN, i['resourceName_string'],i['buffName_string'], i['amount']) for i in bv if i['buffName_string'] <> "Adventure"]
                    star_menu = adventure_list + otheritms_list
                    self._pom_remove_if_exists(pID, pN)
                    self._pom_insert_star_list(pID, pN, star_menu)
                    log.info('gracz/ID %s/%d: zapisano menu gwiazdy, będzie ignorowany kolejne %d sekund'%(pN, pID, self.recent_act.max_age))
                    self.recent_act[ recent_key ] = True
###############################################################################
    class StarItem(object):
        """ pozycja w menu gwiazdy """
        def __init__(self, playerID, playerName, resourceName_string, \
                     buffName_string, amount ):
            self.playerID       = playerID
            self.playerName     = playerName
            self.resourceName_string= resourceName_string
            self.buffName_string= buffName_string
            self.amount         = amount
            self.kiedyZlapanoTS = time().__int__()

        def _sql_ins_data(self):
            """ wypluwa sql insert values:
                (  playerID,          playerName,     resourceName_string,
                   buffName_string,   amount,         kiedyZlapanoTS  )
            """                
            return  self.playerID,              self.playerName,        \
                    self.amount,                self.buffName_string,   \
                    self.resourceName_string,   self.kiedyZlapanoTS
###############################################################################      
                    
from .config import dbcfg as cfg_sgd
sgd=SGD(**cfg_sgd)


###############################################################################
@concurrent
def response(context, flow):
    """========================================================================

 ==========================================================================="""
    if flow.request.host.endswith('.thesettlersonline.pl'):
	if "application/x-amf" in flow.response.headers.get("Content-Type", "_"):
            with decoded(flow.response):
                res = flow.response.content
                if  search( 'defaultGame.Communication.VO.dZoneVO',  res )\
                and search( 'defaultGame.Communication.VO.dBuffVO',  res )\
                and search( 'defaultGame.Communication.VO.dPlayerVO',res ):
                    log.debug("got type 1001 response... wysyłam szpiega...")
                    try:
                        t= Thread(target=sgd._incoming_traffic_handler, args=(flow.response.content,))
                        t.setDaemon(True) 
                        t.start()
                    except (KeyboardInterrupt, SystemExit):
                        log.info('caught either KeyboardInterrupt or SystemExit, quitting threads')
                        t.__stop()
                        import thread
                        thread.interrupt_main()
    
    
