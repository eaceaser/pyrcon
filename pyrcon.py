#!/usr/bin/env python
import argparse
import io
import logging

from yaml import load, dump

from bfserver import BFServer
from gevent import backdoor
from server import simple
from control import Control
from proxy import Proxy

import gevent

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
config_file = io.open(args.config, 'r')
config = load(config_file, Loader=Loader)
config_file.close()

logger.info("Loading maps data.")
maps_file = io.open(args.mapfile, 'r')
map_data = load(maps_file, Loader=Loader)
maps_file.close()

logger.info("Loading mode data.")
mode_file = io.open(args.modefile, 'r')
mode_data = load(mode_file, Loader=Loader)
mode_file.close()

server_config = config['rcon']
server = BFServer(server_config["host"], server_config["port"], server_config["password"])
control = Control(server, config["server"]["password"], map_data, mode_data)

modules_config = config['modules']
if modules_config is not None:
  for module_name in modules_config:
    logger.info("Loading module: %s" % module_name)
    module_config = modules_config[module_name]
    i = __import__("modules.%s" % module_name, globals(), locals(), ['module'], -1)
    i.module(control, module_config)

simple.simpleServer(control)
proxy = Proxy(server)

while True:
  gevent.sleep(100)
