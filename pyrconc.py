#!/usr/bin/env python

import os
import readline
import argparse
import json

import gevent.pool
import gevent.hub
from gevent import socket, queue, event
from gevent import Greenlet

class SimpleJsonClient:
  def __init__(self, hostname, port):
    self._socket = None
    self._hostname = hostname
    self._port = port
    self._send_queue = gevent.queue.Queue()
    self._read_queue = gevent.queue.Queue()
    self._group = gevent.pool.Group()

  def start(self):
    address = (socket.gethostbyname(self._hostname), self._port)
    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self._socket.connect(address)
    self._group.spawn(self._send_loop)

  def _send_loop(self):
    fileobj = self._socket.makefile()
    while True:
      msg = self._send_queue.get()
      line = msg[0]
      rv = msg[1]
      fileobj.write(line)
      fileobj.write("\n")
      fileobj.flush()
      # wait for a response.
      response = fileobj.readline().rstrip()
      rv.set(json.loads(response))

  def listServers(self):
    rv = event.AsyncResult()
    j = { "methodName": "getServerIds" }
    blah = json.dumps(j)
    self._send_queue.put((json.dumps(j), rv))
    return rv

class Context:
  def commands(self):
    return self._validCommands

  def prompt(self):
    return self._prompt

  def execute(self, cmd):
    try:
      cmd = self._validCommands[cmd]
      func = cmd[1]
      return func()
    except KeyError:
      return "Invalid command: %s" % cmd

class RootContext(Context):
  def __init__(self, client):
    self._client = client
    self._prompt = "PyRCon"
    self._validCommands = {
      'ls': ("List Available BF3 Servers", self.listServers)
    }

  def listServers(self):
    rv = self._client.listServers()
    val = rv.get()
    return "\n".join(val["response"])

def printHelp(helpDict):
  for cmd in helpDict:
    helpstring = helpDict[cmd][0]
    print "%s: %s" % (cmd, helpstring)

class Console(Greenlet):
  def __init__(self,client):
    Greenlet.__init__(self)
    self._client = client
    self._contexts = [RootContext(self._client)]

  def _run(self):
    while True:
      prompt = "/".join(map(lambda i: i.prompt(), self._contexts))
      currentContext = self._contexts[-1]
      # NOTE: This currently blocks the runloop.
      s = raw_input("%s> " % prompt)
      if s == "help":
        printHelp(currentContext.commands())
      else:
        rv = currentContext.execute(s)
        print rv

parser = argparse.ArgumentParser(description='Command line client for PyRCon.')
parser.add_argument('--host', '-H', dest='host', help='PyRCon Hostname', default="localhost")
parser.add_argument('--port', '-p', dest='port', help='PyRCon Port', type=int, default=31337)
args = parser.parse_args()

client = SimpleJsonClient(args.host, args.port)
client.start()
g = Console(client)
g.start()
g.join()
