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
args = parser.parse_args()

point = TCP4ClientEndpoint(reactor, args.hostname, args.port)
d = point.connect(FBFactory())
reactor.run()
