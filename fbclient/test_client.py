#!/usr/bin/env python

import argparse

from fbclient import FBClient

from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ClientEndpoint

class FBFactory(Factory):
  def buildProtocol(self, addr):
    return FBClient()

parser = argparse.ArgumentParser(description="Test Frostbite RCon Client.")
parser.add_argument('-H', '--hostname', dest='hostname', help='Server Hostname', required=True)
parser.add_argument('-p', '--port', dest='port', help='Server Port', type=int, default=47200)
args = parser.parse_args()

point = TCP4ClientEndpoint(reactor, args.hostname, args.port)
d = point.connect(FBFactory())
reactor.run()
