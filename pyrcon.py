#!/usr/bin/env python
import argparse
import io
import logging

from yaml import load, dump

from bfserver import BFServer
from gevent import backdoor
from server import simple
from control import Control

try:
  from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
  from yaml import Loader, Dumper

parser = argparse.ArgumentParser(description="PyRCon - Python Battlefield 3 RCon Manager")
parser.add_argument('-c', '--config', dest='config', help='Configuration File', required = True)
parser.add_argument('--mapdata', dest='mapfile', help='Map data file', default='./data/maps.yml')
parser.add_argument('--modedata', dest='modefile', help='Mode data file', default='./data/modes.yml')
parser.add_argument('--verbose', '-v', dest='verbose', action='count', help='Verbose logging.')
args = parser.parse_args()

level = logging.WARNING
if args.verbose == 1:
  level = logging.INFO
elif args.verbose >= 2:
  level = logging.DEBUG

logging.basicConfig(level=level)

logger = logging.getLogger("")
logger.info("Loading config file.")
configFile = io.open(args.config, 'r')
config = load(configFile, Loader=Loader)
configFile.close()

logger.info("Loading maps data.")
mapsFile = io.open(args.mapfile, 'r')
mapData = load(mapsFile, Loader=Loader)
mapsFile.close()

logger.info("Loading mode data.")
modeFile = io.open(args.modefile, 'r')
modeData = load(modeFile, Loader=Loader)
modeFile.close()

serverConfig = config['rcon']
server = BFServer(serverConfig["host"], serverConfig["port"], serverConfig["password"])
control = Control(server, config["server"]["password"], mapData, modeData)

modules_config = config['modules']
for module_name in modules_config:
  module_config = modules_config[module_name]
  i = __import__("modules.%s" % module_name, globals(), locals(), ['module'], -1)
  i.module(control, module_config)

simple.simpleServer(control)
