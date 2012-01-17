#!/usr/bin/env python

import os
import readline
import argparse
import json

import gevent.pool
import gevent.hub
from gevent import socket, queue, event
from gevent import Greenlet

class SimpleJsonClient(object):
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
      jsonResponse = json.loads(response)
      rv.set(jsonResponse["response"])

  def nextRound(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "nextRound" }
    s= json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def getServerInfo(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "info" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

class Context(object):
  def commands(self):
    return self._validCommands

  def prompt(self):
    return self._prompt

  def execute(self, cmd, args):
    try:
      cmd = self._validCommands[cmd]
      argparse = cmd[0]
      argspace = argparse.parse_args(args)
      func = cmd[1]
      return func(argspace)
    except KeyError:
      return "Invalid command: %s" % cmd

class RootContext(Context):
  def __init__(self, client):
    self._client = client
    self._prompt = "PyRCon"

    nextRound = argparse.ArgumentParser(prog='nextround', description="Switch server to the next round.", add_help=False)
    info = argparse.ArgumentParser(prog='info', description="Basic Server Info.", add_help=False)

    self._validCommands = {
      'info': (info, self._serverInfo),
      'nextround': (nextRound, self._nextRound)
    }

  def _serverInfo(self, args):
    rv = self._client.getServerInfo()
    d = rv.get()
    s = ""
    return "\n".join(["%s: %s" % (x, d[x]) for x in d])

  def _nextRound(self, args):
    rv = self._client.nextRound()
    rv.get()
    return "OK"

def printHelp(helpDict):
  for cmd in helpDict:
    argparse = helpDict[cmd][0]
    print argparse.format_help()

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
      parts = s.split(" ")
      cmd = parts[0]
      args = []
      if len(parts) > 1:
        args = parts[1:]

      if cmd == "help":
        printHelp(currentContext.commands())
      elif cmd == "..":
        self._contexts.pop()
      else:
        rv = currentContext.execute(cmd, args)
        if type(rv) == str or type(rv) == unicode:
          print rv
        elif isinstance(rv, Context):
          self._contexts.append(rv)

parser = argparse.ArgumentParser(description='Command line client for PyRCon.')
parser.add_argument('--host', '-H', dest='host', help='PyRCon Hostname', default="localhost")
parser.add_argument('--port', '-p', dest='port', help='PyRCon Port', type=int, default=31337)
args = parser.parse_args()

client = SimpleJsonClient(args.host, args.port)
client.start()
g = Console(client)
g.start()
g.join()
