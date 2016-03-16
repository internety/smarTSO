#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 15 01:40:54 2016
@author: s

    kod odpowiedzialny za analizę poszczególnych zrzutów rynku z tabeli Offki,
    dla każdego z nich generuje statystykę i wrzuca ją do tabeli Offstats
    
    Funkcje:
    
    getRecentTS() 
     - zwraca jako tuple najmłodsze timestampy z tabel Offki oraz Offstats
       używana do sprawdzania czy jest coś do zrobienia, jeśli obie zwrócone
       wartości są identyczne - nie ma nic do zrobienia
       
    getTSSince(odTS)
     - zwraca liste timestampów z tabeli Offki między odTS(wyłącznie) a 
       ostatnio dodanym (włącznie)
       używana do określenia listy TS którym nie obliczono dotychczas statystyk
       
       
       
       
    marketStateGenerator(timestamp)
     - na podstawie tabeli Offki odtwarza stan rynku dla podanej chwili.
     * nie jest to trywialne zadanie, bo wymaga przetworzenia wszystkich wpisów
       z ostatnich 6 godzin...

Parametry połączenia z bazą:
    create_engine( 'mysql://user:password@127.0.0.1:3306/database' )


"""

from sqlalchemy import create_engine, MetaData, Table, and_
from sqlalchemy.sql import func
from sqlalchemy.orm import create_session
from sqlalchemy.ext.declarative import declarative_base


Base     = declarative_base()
engine   = create_engine( 'mysql://s3tt:s3pass@127.0.0.1:3306/s3tt' )
metadata = MetaData( bind=engine )


class Offki(Base):
    __table__ = Table( 'offki', metadata, autoload=True )

class Offstats(Base):
    __table__ = Table( 'offstats', metadata, autoload=True )


global    session
session = create_session( bind=engine )


def getRecentTS():
    """ zwraca jako tuple, najmłodsze `server_source_timestamp` obu tabel,
        w szczególnym wypadku gdy któraś z tabel jest pusta - zwraca dla niej 0
        wynik: (offstats_newest_timestamp, offki_newest_timestamp)
    """
    qry       = session.query( func.max( Offstats.server_source_timestamp ) \
                       .label( "stats_ts" ))
    res       = qry.one()
    stats_ts  = int(res.stats_ts) if res.stats_ts else 0
    
    qry       = session.query( func.max( Offki.server_source_timestamp )    \
                       .label( "off_ts" ))
    res       = qry.one()
    off_ts    = int(res.off_ts) if res.off_ts else 0

    return ( stats_ts, off_ts )
    

def getTSSince(odTS):
    """ zwraca listę timestampów z tabeli 'Offki', zaczynając od timestampa
        występującego PO odTS a kończąc na ostatnio dodanym
    """
    assert type( odTS ) \
        is int, 'getTSRange() oczekuje timestampa (int) jako parametru'

    qry   = session.query(    Offki.server_source_timestamp.distinct() )\
                   .filter(   Offki.server_source_timestamp  >  odTS   )\
                   .order_by( Offki.server_source_timestamp            )
    
    return [ row[0].__int__() for row in qry ]
        

    
def marketStateCalculation(timestamp):
    pass


def fetchMarketFromSQL(timestamp):
    """ przyjmuje timestampa, ładuje z tabeli 'Offki'
        dane dla wybranego timestampa
        zwraca listę wierszy tabeli.
    """
    assert type( timestamp ) \
        is int ,'getPendingTS() oczekuje liczby (timestampa) jako parametru'

    qry   = session.query(    Offki.server_source_timestamp.distinct()  ) \
                   .filter(   Offki.server_source_timestamp  >  startTS ) \
                   .filter(   Offki.server_source_timestamp  <= endTS   ) \
                   .order_by( Offki.server_source_timestamp             )
                   
    res   = qry.all()              
    listaTS = [ list(row) for row in qry ]

    for t in listaTS:  
        if t[0]: 
            chronolista.append( t[0].__int__())

    return chronolista







    qry    = session.query(                                           \
                func.count(  Offki.server_source_timestamp ),         \
                             Offki.server_source_timestamp )
    
    qry    = session.query(                                           \
                func.count(  Offki.server_source_timestamp ),         \
                             Offki.server_source_timestamp )          \
                    .filter( Offki.server_source_timestamp  > startTS,\
                             Offki.server_source_timestamp <= endTS   )

    qry    = session.query(  Offki.server_source_timestamp    )       \
                    .filter( Offki.server_source_timestamp >  startTS,\
                             Offki.server_source_timestamp <= endTS   )

session.query(func.count(Offki.co), Offki.co).group_by(Offki.co).all()
sss=session.query( func.count( Offki.server_source_timestamp), \
                               Offki.server_source_timestamp)  \
                    .group_by( Offki.server_source_timestamp).all()
                    
                    
    qry    = session.query( Offki.server_source_timestamp.distinct()   ) \
                    .filter( Offki.server_source_timestamp  >  startTS ) \
                    .filter( Offki.server_source_timestamp  <= endTS   ) \
                    .order_by( Offki.server_source_timestamp ) \
                    .all()
                    
                        datetime.utcnow().date())
                               Offki.server_source_timestamp)  \
                    .group_by( Offki.server_source_timestamp).all()

sss=session.query(Offki.server_source_timestamp, func.count(Offki.server_source_timestamp)).filter( Offki.server_source_timestamp >  startTS ).all()



    res       = qry.all()
    wynik     = {}
    for stamp in res:
        if licznik and stamp:
            wynik [ stamp.__int__() ] = licznik.__int__()
        else:
            break        
    return wynik
    
    
    
def processMarketChanges(tradict):
    """ przyjmuje timestamp, odczytuje jego dane z 'Offki', wylicza statystyki,
        efekty zapisuje w 'Offstats'
    """    
    pass

def makeStats(ts):
    """ przyjmuje timestamp, odczytuje jego dane z 'Offki', wylicza statystyki,
        efekty zapisuje w 'Offstats'
    """    
    pass
    
    
def getBestCorrelations(ts):
    """ 
        DRAFT    
        przyjmuje server_source_timestamp dla którego oblicza pomocnicze dane
        z tabeli `Offki`.
        zwraca tupla uporządkowanych, sortowanych malejąco słownikow, po jednym
        dla każdej ze stron ofert
        wynik: 
        ({oferowany prod.: w_ilu_ofertach,...},{żądany prod.: w_ilu_ofertach,...})
    
    """
    qry       = session.query(  Offki.co,    Offki.ile,   \
                                Offki.zaCo,  Offki.zaIle, \
                                Offki.ONEco_rowne_xzaco,  \
                                Offki.xco_rowne_ONEzaco,  \
                                Offki.offer_age_sec,      \
                                Offki.sold_per_hour      )\
                       .filter( Offki.server_source_timestamp == ts )
    res       = qry.all()                   
                       







    qry = session.query(Offki.co)\
          .filter(Offki.server_source_timestamp == ts)
    res = qry.all()

    left = []
    for r in res:
        ls, rs = r
        left.append(ls)
        right.append(rs)
        
        
            
            
    offstats_q = session.query(Offstats)
    offstats_q.


    for instance in sesjaDB.query(Offstats):
        print(instance.co, instance.zaCo)
















