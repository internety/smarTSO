#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
  ver 2016.09.13.2248  /  @author: s
====================================================
- wrzuca handel do SQL w regularnych odstępach czasu
- schema tabeli ofert handlu - plik oferta.table.sql
- przechwytuje i ponawia żądania aktualizacji handlu
  wysłane przez graczy.
- wykrywa serwer (realm) którego dotyczą dane


#####  parametry konfiguracji instancji TradeDumper'a  #####


            
TTD("realmName", **cfg_ttd)

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
from threading2 import Thread, Timer
from re2 import search
from attrdict import AttrDict
from pymysql import connect
from sqlite3 import connect as sq3conn
from os import path
from time import time
from lru import LRU
from collections import namedtuple
from operator import attrgetter
from sys import stdout
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
    hdlr = logging.FileHandler(path.join(BASEDIR,'TradeDumper.log'))
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
   
class TTD(object):
    """ TSO Trade Dumper """    

    def __init__(self, rName, **kwargs):
        cfg_defaults= { 'trSize' : 64,
                        'mmatch' : 64,
                        'watchT' : 30, 
                        'reqryT': 120,
                        'mysql_user' : None,
                        'mysql_pass' : None,
                        'mysql_db' : None,
                        'mysql_host' : None,
                        'bindings_sqlite_file': None}
        self.c = AttrDict()
        for k in cfg_defaults.keys():
            if kwargs.has_key(k):
                self.c[k]=kwargs[k]
            elif cfg_defaults[k]:
                self.c[k]=cfg_defaults[k]
                log.info("przyjęto domyślne ustawienie dla %s"%k)
            else:
                raise Exception("ustawienia niekompletne, brak %s"%k)
        self.updatecounter = 0
        self.uoczerIterCounter=0
        self.c.realmname = rName
        self.c.lastupdatedTS = 0
        self.c.treqs = LRU( self.c.trSize )
        self.db = connect(self.c.mysql_host, 
                            self.c.mysql_user, 
                            self.c.mysql_pass,
                            self.c.mysql_db )
        self.db.autocommit(False)
        self.db.ping(reconnect=True)
        self.market = []
        
        ## wczytuje bindy dla danego realm
        bind = namedtuple('bind', 'playN, playID, realm')
        try:
            with sq3conn(self.c.bindings_sqlite_file) as conn:
                cur = conn.cursor()
                cur.execute("SELECT pN, pID, rN FROM pid_name_realm_map WHERE rN == '%s'" %self.c.realmname)
                self.c.binds = { b for b in map( bind._make, cur.fetchall()) }
                if len( self.c.binds ) < 100:
                    log.warn("realm '%s' has only %d binds! you have been warned..."%( self.c.realmname, len( self.c.binds )))
                else:
                    log.debug("loaded realm '%s': %d binds"%( self.c.realmname, len( self.c.binds )))
            conn.close()
        except:
            raise Exception("błąd ładowania bindów dla %s z %s (sqlite)"\
                            %(self.c.realmname, self.c.bindings_sqlite_file))
        ## bindy załadowane...
        self._uoczer()
                
        
    @staticmethod
    def now():
        """ zwraca time() jako integer (sekund od początku epoki) """
        return time().__int__()
        
  
    def _bindings_test_matching(self, trade_resp_body):
        ''' przyjmuje listę słowników-ofert (w formacie jaki występuje w AMF),
            self.minmatches - ilość trafień wymaganych by uznać wynik 
            zwraca nazwę realm (str), uczy się nowych bindów (do pnrdb[SQLite])
            zwraca None przy niepowodzeniu...
        '''
        bind = namedtuple('bind', 'playN, playID, realm')
        newoffers = trade_resp_body['data']['data']['tradeOffers']
        bindy_handlu = { b for b in map(bind._make, [(o['senderName'], o['senderID'], self.c.realmname) for o in newoffers]) }
        wspolne = bindy_handlu & self.c.binds
        if len(wspolne) >= self.c.mmatch:
            nowe_do_dodania = bindy_handlu - wspolne
            self._bindings_update(nowe_do_dodania)
            log.info('realm %s matched!, %s matches, %s new' %(self.c.realmname, len(wspolne), len(nowe_do_dodania)))
            return True
        else:
            return False
                
        
    def _bindings_update(self, nowy_set):
        """ wpisuje bindy nowe_do_dodania (tuple(pN,pID,rN)) do bazy oraz do self.c.binds  """
        with sq3conn(self.c.bindings_sqlite_file) as conn:
            cur = conn.cursor()
            sql="INSERT INTO pid_name_realm_map (pN,pID,rN) VALUES (?,?,?)"
            cur.executemany(sql, nowy_set)
        conn.close()
        self.c.binds = self.c.binds | nowy_set
        
    def _trade_refresh_needed(self):
        """ true jeśli od odświerzenia handlu minęło> self.c.reqryT inaczej false
        """
        now = self.now()
        log.info('last refresh %ds ago, (reqryT=%d)'%(now-self.c.lastupdatedTS, self.c.reqryT))
        log.info(now-self.c.lastupdatedTS > self.c.reqryT)
        return now-self.c.lastupdatedTS > self.c.reqryT
        

    def _amf_raw_response_parser(self, rawamf):
        """ przetwarza surową odpowiedź AMF (iteruje po zawartych wiadomościach
            (message), wybiera tą o numerze 1061 (trade update), zwraca body pierwszej
            pasującej lub None) """
        decresp = amfdec.decode_packet( rawamf )
        for m in decresp.messages:
            if m.body.body.has_key('type') and int(m.body.body['type'])== 1061 \
            and m.body.body.has_key('data') and m.body.body['data'].has_key('data')\
            and isinstance(m.body.body['data']['data'], dict):
                    if m.body.body['data']['errorCode']==0:
                        return m.body.body
                    else:
                        errcode = m.body.body['data']['errorCode']
                        log.error('amf error, code:%s') %errcode
        return None
        
        
    def _uoczer(self):
        """ "ten co czai" :) :: perform once-upon-a-time checks and cleanups ::
            - sprawdza czas ostatnich odświerzeń rynków każdego z realmów
            - dla przestarzałych emituje duplikaty, jeśli są dostępne
            - planuje kolejne uruchomienie siebie przy pomocy threading.Timer
        """
        self.uoczerIterCounter+=1
        try:                    #  performing timed checks and cleanups
            if self.now()-self.c.lastupdatedTS > 3000 and self.uoczerIterCounter % 1000 == 0:
                log.info('PINGING DATABASE')
                self.db.ping()
        
            if self._trade_refresh_needed() and self.c.treqs:
                recent_key    = self.c.treqs.keys()[0]
                recent_request= self.c.treqs[recent_key]
                raw_trade_response= recent_request.execute()
                if raw_trade_response:
                    parsed_response_body= self._amf_raw_response_parser(raw_trade_response)
                    self._trade_update_market(parsed_response_body)
                    log.info('trade updated with duplicated treq (uID: %d)'%recent_key)
                else:
                    log.info('trade requery failed, deleting treq (uID %d)'%recent_key)
                    del self.c.treqs[recent_key]

        except (KeyboardInterrupt, SystemExit):  # stop on interrupts
            log.info('caught either KeyboardInterrupt or SystemExit, quitting thread')
            import thread
            thread.interrupt_main()
            exit()

        finally:
            log.debug('scheduling run in %ds'%self.c.watchT)
            self.uoczertimer = Timer(self.c.watchT, self._uoczer) # reschedule run
            self.uoczertimer.setDaemon(True)                    # with abort at shutdown
            self.uoczertimer.start()
            
            
    def _incoming_traffic_handler(self, context, flow):
        """ logika postępowania z przechwyconym ruchem (request/response) """
        trade_resp_body  = self._amf_raw_response_parser(flow.response.content)
        if not self._bindings_test_matching(trade_resp_body):
            log.info('ignoring trade data due to realm not identified')
            return None
        
        treq = self.TRequest( context, flow )
        self.c.treqs[ treq.uID ] = treq
        
        self._trade_update_market( trade_resp_body )

    def market_research_a (self, offerlist):
        """ znajduje prosty zysk czyli zacjuodzące offki """
        co    = set([ o.co    for o in offerlist ])
        zaco  = set([ o.za_co for o in offerlist ])
        cozaco= list(set([(o.co, o.za_co)  for o in offerlist ]))
        wyniki  = []

        #??? cozaco = [(i[0], i[1]) for i in cozaco if not (i[1], i[0]) in cozaco]
        for i in cozaco:
            rev = (i[1], i[0])
            if rev in cozaco:
                cozaco.remove(rev)
       ###
       
        for i in cozaco:
            co, zaco = i
            b4cozacolist = [o for o in offerlist if o.co == co and o.za_co == zaco]
            b4zacocolist = [o for o in offerlist if o.co == zaco and o.za_co == co]

            if b4cozacolist and b4zacocolist:
                b4cozaco  = sorted(b4cozacolist, key=attrgetter('xco_eq_onezaco'))[0]
                b4zacoco  = sorted(b4zacocolist, key=attrgetter('xco_eq_onezaco'))[0]
                b4cozacox = b4cozaco.xco_eq_onezaco
                b4zacocox = b4zacoco.xco_eq_onezaco
                if b4cozacox * b4zacocox > 1:
                    wyniki.append((b4cozaco, b4zacoco))
        print wyniki
        return wyniki
    
    def _trade_update_market( self, trade_resp_body ):
        """
        ...
        """
        junk= ['deleted', 'coolDownTime', 'isTradeCancled', 'removed', \
                         'receiverID','offerAcceptedID','remainingTime'] # useless keys
        tradea = trade_resp_body['data']['data']['tradeOffers']
        tradeb = [dict((k, v) for k,v in d.iteritems() if k not in junk) for d in tradea] # usuwam bezużyteczne klucze
        tradec = [dict(map( lambda(k,v): ("r_"+str(k), v), o.items())) for o in tradeb] # nadaje prefix "r_" pierwotnym kluczom
        servercurrenttime = trade_resp_body['data']['data']['currentTime']
        
        sts = servercurrenttime/1000
        now = self.now()
        diff= now - sts
        if abs(diff) > 300:
            log.warn("UWAGA!: czas serwera %s przesunięty o %d sekund względem nas!!! "%(self.c.realmname, diff))
        
        for o in tradec:
            o['realmName']=self.c.realmname
            o['servercurrtime']=servercurrenttime
        captured = [ self.Offer(**o) for o in tradec ]
        i_captured = len(captured)
        moje_bez_wygaslych = [ o for o in self.market if not o.is_expired ]
        i_moje = len(self.market)
        i_wygaslo = i_moje - len(moje_bez_wygaslych)
        znikniete = [ o for o in moje_bez_wygaslych if not o in captured ]
        i_znikniete = len(znikniete)
        do_dodania = [o for o in captured if not o in self.market]
        i_do_dodania = len(do_dodania)
        log.debug('%d pamietane, z czego %d wygasło'%(i_moje, i_wygaslo))
        log.debug('%d przechwycone, w tym %d nowych, %d znikło'%(i_captured, i_do_dodania, i_znikniete))

        #sql_znik_data_list = [o._sql_ins_zniknij() for o in znikniete]
        sql_ins_data_list = [o._sql_ins_data for o in do_dodania]
        ile_zmian = len(sql_ins_data_list)
        log.debug('sql: %d wierszy do wpisania (nowe+zmienione)'%ile_zmian)
        sql= """INSERT IGNORE INTO oferta 
             ( r_id,            r_senderID,     r_created,      r_slotPos,
               r_slotType,      r_offer,        r_senderName,   r_type,
               r_lotsRemaining, realmName,      updated_ts,     created_ts,
               expires_ts,      co,             za_co,          ile, 
               za_ile,          oneco_eq_xzaco, xco_eq_onezaco, lots_sold,
               lots_sent,       age_sec,        sold_per_hr ) 
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        #if self.market:
        #    self.c.cur.executemany(sql, sql_znik_data_list)
        db = connect(self.c.mysql_host, 
                            self.c.mysql_user, 
                            self.c.mysql_pass,
                            self.c.mysql_db )
        db.autocommit(False)
        db.ping(reconnect=True)
        
        cur = db.cursor()
        cur.executemany(sql, sql_ins_data_list)
        db.commit()
        db.close()
        
        self.market = captured
        self.c.lastupdatedTS = self.now()
        self.updatecounter += 1
        log.info('updatecounter %d'%self.updatecounter)
        
        t= Thread(target=self.market_research_a, args=(captured,))
        t.setDaemon(True)
        t.start()        
        
###############################################################################
    class Offer(object):
        """ oferta handlowa """
        def __init__(self, r_offer, r_slotPos, r_created, r_type, r_senderID,\
                     r_senderName, r_lotsRemaining, r_id, r_slotType, realmName,\
                     servercurrtime):
            self.r_offer    = r_offer
            self.r_slotPos  = r_slotPos
            self.r_created  = r_created
            self.r_type     = r_type
            self.r_senderID = r_senderID
            self.r_senderName=r_senderName
            self.r_lotsRemaining= r_lotsRemaining
            self.r_id       = r_id
            self.r_slotType = r_slotType
            self.realmName  = realmName
            self.servercurrtime= servercurrtime
            self.updated_ts = servercurrtime /1000
            self.created_ts = r_created/1000
            coile,zacoile,\
                  lots_sent = r_offer.split('|')
            self.lots_sent  = int(lots_sent)
            self.co,self.ile= self._parsei(coile)
            self.za_co,\
                 self.za_ile= self._parsei(zacoile)
            self.oneco_eq_xzaco= float(self.za_ile) /self.ile
            self.xco_eq_onezaco= 1 /self.oneco_eq_xzaco
            self.lots_sold  = self.lots_sent - self.r_lotsRemaining
            self.age_sec    = (self.servercurrtime - self.r_created)/1000
            self.sold_per_hr= self.lots_sold /(float(self.age_sec) /3600)
            self.expires_ts = self.created_ts +21600     # 6 godzin w sekundach
        
        @property    
        def _sql_ins_data(self):
            """ wypluwa sql insert values:
            ( r_id,            r_senderID, r_created,    r_slotPos,
              r_slotType,      r_offer,    r_senderName, r_type,
              r_lotsRemaining, realmName,  updated_ts,   created_ts,
              expires_ts,      co, za_co,  ile, za_ile,  oneco_eq_xzaco,
              xco_eq_onezaco,  lots_sold,  lots_sent,    age_sec, 
              sold_per_hr)                    
            """
            return  self.r_id,                        self.r_senderID,              \
                    self.r_created,                   self.r_slotPos,               \
                    self.r_slotType,                  self.r_offer,                 \
                    self.r_senderName.encode('utf8'), self.r_type,                  \
                    self.r_lotsRemaining,             self.realmName.encode('utf8'),\
                    self.updated_ts,                  self.created_ts,              \
                    self.expires_ts,                  self.co, self.za_co,          \
                    self.ile, self.za_ile,            self.oneco_eq_xzaco,          \
                    self.xco_eq_onezaco,              self.lots_sold,               \
                    self.lots_sent,                   self.age_sec,                 \
                    self.sold_per_hr
        
        @property
        def _sql_ins_zniknij(self):
            """ sql insert values dla znikniętych ofert (r_lotsRemaining=0) """
            znik = list(self._sql_ins_data())
            znik[8]=0
            return tuple(znik)
            
        @staticmethod
        def _parsei(p):
            """ parsuje ofertę TSO (string) na tuple(produkt, ilość)
                przy niepowodzeniu zwraca tuple('niesparsowany string', 1) 
                NOWA WERSJA z 11 wrz 2016, parsuje każdą ilość budynków     """
            c = p.count(',')
            o = p.split(',')
            if c==1:
                return (o[0],int(o[1]))
            if o[1]:
                i=':'.join([o[0],o[1]])
                return (i,1) if 'Adventure' in o[0] else (i,int(o[2]))
            else:
                return (o[0],int(o[2]))
            log.error ("Parsing rawoffer '%s' failed")%p
            return ("(%s)"%p,1)
            
        @property
        def is_expired(self):
            return self.expires_ts < time().__int__()

            
        def __repr__(self):
            """ reprezentacja tekstowa oferty """
            return "<Offer( ID:{rid:<10d} sID:{sid:<10d} sName:{sn:<16s} sold:{sold:<2d} lotsPerHour:{lph:<3.8f} offer:{off})>" \
                   .format( rid = self.r_id,
                            sid = self.r_senderID,
                            sn  = self.r_senderName.encode('utf8'),
                            sold= self.lots_sold,
                            lph = self.sold_per_hr,
                            off = self.r_offer.encode('utf8') )
                   
                   
        def __eq__(self, o):
            return self.r_id == o.r_id \
               and self.r_created == o.r_created \
               and self.r_lotsRemaining == o.r_lotsRemaining \
               and self.realmName == o.realmName

###############################################################################
    class TRequest(object):
        """ przechwycone na drodze klient->serwer pytanie o stanu rynku
            (zawiera: 'ctx', 'flow', weryfikację poprawnych odpowiedzi)  
            -----------------------------------------------------------
            execute()   - wysyła duplikat żądania świeżych danych rynku
                          zwraca odpowiedź lub False przy niepowodzeniu
            uID         - ID gracza który wysłał oryginał
            capturedTS  - timestamp przechwycenia oryginału
            duplicatedTS- timestamp ostatniego wysłania duplikatu
            ----------------------------------------------------------- """            
        def __init__(self, ctx, flo):
            assert ctx.__class__.__name__ == "ScriptContext", "ctx: expected 'ScriptContext'"
            assert flo.__class__.__name__ == "HTTPFlow", "flo: expected 'HTTPFlow'"
            decoded_request = amfdec.decode_packet( flo.request.content )
            self.uID = decoded_request.messages[0].body[0].body[0]['dsoAuthUser']
            self.ctx = ctx
            self.flo = flo
            self.capturedTS = time().__int__()
            self.duplicatedTS = None
    
            
        def execute(self):
            self.duplicatedTS = time().__int__()
            flo = self.ctx.duplicate_flow(self.flo)
            self.ctx.replay_request(flo)
            treq_age = time().__int__() - self.capturedTS
            debugmsg = 'sent TReq duplicate (uID:%d, captured %ds ago)'\
                                                          %(self.uID, treq_age)
            verified = self._vrfy_response( flo.response.content )
            if not verified:
                log.warning (debugmsg+' result: FAIL!' )
                return False
            else:
                log.debug (debugmsg+' result: OK' )
                return verified            
                
                
        def _vrfy_response(self, r):
            """ szuka stringów występujących tylko w poprawnych odpowiedziach,
                jeśli występują przekazuje odpowiedź, jeśli nie -> False
            ----------------------------------------------------------------"""
            return r if search('userAcceptedTradeIDs',r) and search('tradeOffers',r)\
            and search('defaultGame.Communication.VO.TradeWindow.dTradeWindowResultVO',r)\
            else False

            
from .config import dbcfg
cfg_ttd= { 'trSize' : 64,
           'mmatch' : 25,
           'watchT' : 29, 
           'reqryT': 300,
           'bindings_sqlite_file': path.join(BASEDIR,'sqlite_pnr.db')  }
cfg_ttd.update(dbcfg)
            
ttd=TTD("Kolonia", **cfg_ttd)


###############################################################################
@concurrent
def response(context, flow):
    """========================================================================
    "Called when a server response has been received"... łapię wyłącznie
    odpowiedzi, bo interesują mnie zestawy (request/response). Przechwycony
    response wraz z requestem wchodzą w skład transakcji, reprezentowanej przez
    mitmproxy.models.HTTPFlow()
    "HTTPFlow is collection of objects representing a single HTTP transaction".
    Więcej info na WWW:  http://docs.mitmproxy.org/en/stable/dev/models.html
 ==========================================================================="""
    if flow.request.host.endswith('.thesettlersonline.pl'):
        if "application/x-amf" in flow.response.headers.get("Content-Type", "_"):
            with decoded(flow.response):
                res = flow.response.content
                req = flow.request.content
                if  search( 'defaultGame.Communication.VO.TradeWindow.dTradeWindowResultVO', res )\
                and search( 'userAcceptedTradeIDs', res ) and search( 'tradeOffers', res )\
                and search( 'GetAvailableOffers', req ):
                    log.debug("got trade REQ/RESP pair, feeding TDD thread...")
                    try:
                        t= Thread(target=ttd._incoming_traffic_handler, args=(context, flow,))
                        t.setDaemon(True) 
                        t.start()
                    except (KeyboardInterrupt, SystemExit):
                        log.info('caught either KeyboardInterrupt or SystemExit, quitting threads')
                        t.__stop()
                        import thread
                        thread.interrupt_main()
    
    

