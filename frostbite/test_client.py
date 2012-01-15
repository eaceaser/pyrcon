#!/usr/bin/env python2

import argparse
import sys

from fbclient import FBClient, FBClientFactory

from twisted.application import internet
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.python import log

log.startLogging(sys.stdout)

parser = argparse.ArgumentParser(description="Test Frostbite RCon Client.")
parser.add_argument('-H', '--hostname', dest='hostname', help='Server Hostname', required=True)
parser.add_argument('-p', '--port', dest='port', help='Server Port', type=int, default=47200)
parser.add_argument('-P', '--password', dest='password', help='Server Password', required=True)
#parser.add_argument('-s', '--say', dest='message', help='Send an admin message')
args = parser.parse_args()

def gotProtocol(p):
  p.serverInfo()
  p.version()
  p.login()
  p.adminSayAll("greetings noobs")

internet.TCPClient(args.hostname, args.port, FBClientFactory)
