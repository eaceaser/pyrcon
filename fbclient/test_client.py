#!/usr/bin/env python

import argparse
import sys

from fbclient import FBClient, FBFactory

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.python import log

log.startLogging(sys.stdout)

parser = argparse.ArgumentParser(description="Test Frostbite RCon Client.")
parser.add_argument('-H', '--hostname', dest='hostname', help='Server Hostname', required=True)
parser.add_argument('-p', '--port', dest='port', help='Server Port', type=int, default=47200)
parser.add_argument('-P', '--password', dest='password', help='Server Password', required=True)
args = parser.parse_args()

def gotProtocol(p):
  p.serverInfo()
  p.version()
  p.login()

point = TCP4ClientEndpoint(reactor, args.hostname, args.port)
d = point.connect(FBFactory(args))
d.addCallback(gotProtocol)
reactor.run()
