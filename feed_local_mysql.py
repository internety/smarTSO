#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
## - testowy kod wrzucający handel do SQL
##   REQUIRES: amfast, libmproxy, re2, umysqldb
## - to jest skrypt inline dla mitmdump, usage: 'mitmdump -p [PORT] -s [skrypt]'
## - definicja tabeli SQL wraz z komentarzami w pliku table-offki.sql
"""

# ustawienia połączenia z bazą
db_host='127.0.0.1'
db_user='s3tt'
db_pass='s3pass'
db_name='s3tt'


from amfast import decoder as amfdec
from threading import Thread
from libmproxy.script import concurrent
from libmproxy.models import decoded
from sys import stdout
import logging, re2, umysqldb
global log, db, cur


def DBinit(db_h, db_u, db_p, db_n):
    """ zwraca w postaci tupla objekty: baze (db) oraz kursor db.cursor()
    """
    db=umysqldb.connect(db_h, db_u, db_p, db_n)
    db.autocommit(False)
    return db, db.cursor()
db, cur = DBinit(db_host, db_user, db_pass, db_name)


def setlogger():
    ''' na podstawie https://docs.python.org/2/howto/logging-cookbook.html
    '''
    log            = logging.getLogger( )
    log.setLevel   ( logging.DEBUG )
    ch             = logging.StreamHandler( stdout )
    ch.setLevel    ( logging.DEBUG )
    formatter      = logging.Formatter( '%(asctime)s - %(name)s - %(levelname)s - %(message)s' )
    ch.setFormatter( formatter )
    log.addHandler ( ch )
    return log
log = setlogger()


def parseitem(partoff):
    """ sedno każdej jednostkowej oferty handlowej, prócz mniej ważnych,
        z punktu widzenia handlujących, detali, zawiera podstawową informację o
        ofercie: CO? (produkt), ILE?, ZaCo? (płatność), ZaIle? (cena)
        ta funkcja wyławia te informacje z ofert.
        
        przyjmuje: string, część oferty spomiędzy znaków |
        zwraca: tuple (produkt, ilość)
    """
    if  partoff.count(',') is 1:         # zawiera 1 przecinek?
        return tuple(partoff.split(',')) # tak? czyli najprostsza notacja
    elif partoff[:9] in ['Adventure', 'BuildBuil']: # budynki/przygody
        item, b, c, d, e= partoff.split(',')[:5]
        if b: item=','.join([item, b])   
        return item, 1
    elif partoff.count(',') is 4:       # poniżej już tylko premie,
        item, b, c, d, e= partoff.split(',')  # w tym dosypki.
        if b: item=','.join([item, b])
        if 'FillDeposit' in item:
            return item, d
        else:
            return item, e
    else:
        log.warning( "cannot parse ", partoff)
        return partoff, 1


def DBinsert(rawamf):
    mess = amfdec.decode_packet(rawamf)
    nest = mess.messages[0].body.body['data']['data']
    listaofert = nest['tradeOffers']
    source_timestamp = nest['currentTime']
    manyoffers=[]
    for o in range(len(listaofert)):
        raw_offerID              = listaofert[o]['id']
        raw_senderID             = listaofert[o]['senderID']
        raw_senderName           = listaofert[o]['senderName']
        raw_type                 = listaofert[o]['type']
        raw_created              = int("%.0f"%float( listaofert[o]['created']/1000 ))
        raw_lotsRemaining        = listaofert[o]['lotsRemaining']
        raw_offer                = listaofert[o]['offer']
        raw_offer_coile, \
            raw_offer_zacoile, \
            raw_offer_transze    = raw_offer.split('|')
        raw_offer_transze        = int( raw_offer_transze )
        
        #source_timestamp jest milisekundach, my dbamy o sekundy czyli /1000
        server_source_timestamp  = int("%.0f"%float( source_timestamp/1000 ))
        
        lots_sold                = raw_offer_transze - raw_lotsRemaining
        offer_age_sec            = server_source_timestamp - raw_created
        sold_per_hour            = float( lots_sold ) / ( offer_age_sec / 3600 )
        
        co, Ile                  = parseitem( raw_offer_coile )
        zaco, zaIle              = parseitem( raw_offer_zacoile )
        
        ONEco_rowne_Xzaco        = float( zaIle ) / int( Ile )
        Xco_rowne_ONEzaco        = 1 / ONEco_rowne_Xzaco
          
        params=(    raw_offerID, \
                    raw_senderID, \
                    raw_senderName, \
                    raw_type, \
                    raw_created, \
                    raw_lotsRemaining, \
                    raw_offer, \
                    raw_offer_transze, \
                    server_source_timestamp, \
                    co, \
                    zaco, \
                    Ile, \
                    zaIle, \
                    ONEco_rowne_Xzaco, \
                    Xco_rowne_ONEzaco, \
                    lots_sold, \
                    offer_age_sec, \
                    sold_per_hour )

        manyoffers.append(params)

    sql = """INSERT IGNORE INTO offki ( raw_offerID,
                                        raw_senderID, 
                                        raw_senderName, 
                                        raw_type, 
                                        raw_created, 
                                        raw_lotsRemaining, 
                                        raw_offer, 
                                        raw_offer_transze, 
                                        server_source_timestamp, 
                                        co,  
                                        zaco,
                                        Ile, 
                                        zaIle,
                                        ONEco_rowne_Xzaco,
                                        Xco_rowne_ONEzaco,
                                        lots_sold,
                                        offer_age_sec, 
                                        sold_per_hour)
          VALUES ( %s, %s, %s, %s,
                   %s, %s, %s, %s,
                   %s, %s, %s, %s,
                   %s, %s, %s, %s,
                   %s, %s )"""

    cur.executemany( sql, manyoffers )    
    db.commit()
    

@concurrent
def response(context, flow):
    """
       Called when a server response has been received.
    """
    if "application/x-amf" in flow.response.headers.get("content-type", "") \
    and re2.search(  r'.thesettlersonline.pl/GameServer', flow.request.pretty_url) \
    and flow.request.method is 'POST' \
    and re2.search(r'defaultGame.Communication.VO.dServerActionResult', flow.response.content) \
    and re2.search(r'defaultGame.Communication.VO.TradeWindow.dTradeWindowResultVO', flow.response.content) \
    and re2.search(r'tradeOffers', flow.response.content) \
    and re2.search(r'userAcceptedTradeIDs', flow.response.content) \
    and re2.search(r'defaultGame.Communication.VO.TradeWindow.dTradeObjectVO', flow.response.content):
        with decoded(flow.response):   
            try:
                t = Thread(target=DBinsert, args=(flow.response.content,))
                t.daemon = True
                t.start()
            except (KeyboardInterrupt, SystemExit):
                t.__stop()
