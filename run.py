#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 15 02:02:00 2016
@author: s
"""
import sys

from mitmproxy import dump, proxy

class TSOproxy(dump.DumpMaster):
  def run(self):
    try:
      dump.DumpMaster.run(self)
    except KeyboardInterrupt:
      self.shutdown()

opcje = dump.Options()
opcje.scripts= [ 'TradeDumper.py', 'SzpieGwiazdor.py', 'XMPPUserAuth.py']
#opcje.scripts= [ 'TradeDumper.py', 'SzpieGwiazdor.py', ]
config= proxy.ProxyConfig  (port=5310,  host='' )
server= proxy.server.ProxyServer(config)

print "Launching TSOProxy at localhost:5310"
print "scripts loaded: %s "%str(opcje.scripts)

try:
    harvester= TSOproxy(server, opcje)
    harvester.run()
except dump.DumpError as dumperr:
    print(str(dumperr))
    sys.exit(dumperr)
except KeyboardInterrupt:
    pass
