#!/usr/bin/env python
import argparse
import io
import logging

from yaml import load, dump

from bfserver import BFServer

try:
  from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
  from yaml import Loader, Dumper

parser = argparse.ArgumentParser(description="PyRCon - Python Battlefield 3 RCon Manager")
parser.add_argument('-c', '--config', dest='config', help='Configuration File', required = True)
parser.add_argument('--verbose', '-v', dest='verbose', action='count', help='Verbose logging.')
args = parser.parse_args()

level = logging.WARNING
if args.verbose == 1:
  level = logging.INFO
elif args.verbose == 2:
  level = logging.DEBUG

logging.basicConfig(level=level)

configFile = io.open(args.config, 'r')
config = load(configFile, Loader=Loader)
configFile.close()

print config
for serverConfig in config['servers']:
  server = BFServer(serverConfig["host"], serverConfig["port"], serverConfig["password"])
