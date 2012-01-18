#!/usr/bin/env python

import os
import readline
import argparse
import json

import gevent.pool
import gevent.hub
from gevent import socket, queue, event
from gevent import Greenlet

class ParsingError(Exception):
  pass

class InternalParser(argparse.ArgumentParser):
  def exit(self, status=0, message=None):
    raise ParsingError

  def _print_message(self, message, file=None):
    if message:
      if file is None:
        file = _sys.stdout
      file.write(message)

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
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def getServerInfo(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "info" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def getVersion(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "version" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def restartRound(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "restartRound" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def listMaps(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "listMaps" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def listMapIndices(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "getMapIndices"}
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def addMap(self, name, gamemode, rounds):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "addMap" }
    j["arguments"] = [name, gamemode, rounds]
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def knownMaps(self):
    rv = event.AsyncResult()
    j = { "server": False, "methodName": "knownMaps" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def setNextMap(self, position):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "setNextMap", "arguments": [position] }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def clearMaps(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "clearMapList" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def listPlayers(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "listPlayers" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def teams(self):
    rv = event.AsyncResult()
    j = { "server": False, "methodName": "listTeams" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

class Context(object):
  def help(self, cmd=None):
    if cmd is None:
      for i in self._parsers:
        self._parsers[i].print_help()
    else:
      parser = self._parsers[cmd]
      parser.print_help()

  def prompt(self):
    return self._prompt

  def execute(self, cmd, args):
    try:
      parse = self._parsers[cmd].parse_args(args)
      return parse.func(parse)
    except KeyError:
      return "%s is an invalid command." % cmd
    except ParsingError:
      return "%s has invalid arguments." % (" ".join(args))

class RootContext(Context):
  def __init__(self, client):
    self._client = client
    self._prompt = "PyRCon"

    nextRound = InternalParser('nextround', description="Switch server to the next round.", usage="nextround: Switch server to the next round.", add_help=False)
    nextRound.set_defaults(func=self._nextRound)

    restartRound = InternalParser('restartround', description="Restart current round.", add_help=False)
    restartRound.set_defaults(func=self._restartRound)

    info = InternalParser('info', description="Basic Server Info.", usage="info: Basic Server Info.", add_help=False)
    info.set_defaults(func=self._serverInfo)

    version = InternalParser('version', description="Server Version.", usage="version: BF3 Server Version.", add_help=False)
    version.set_defaults(func=self._version)

    maps = InternalParser('maps', description="BF3 Server Map List Context", add_help=False)
    maps.set_defaults(func=self._maps)

    player = InternalParser('player', description="Player List Context", add_help=False)
    player.set_defaults(func=self._player)

    knownmaps = InternalParser('knownmaps', description="Known Maps.", add_help=False)
    knownmaps.set_defaults(func=self._knownMaps)

    teams = InternalParser('teams', description="Current Teams.", add_help=False)
    teams.set_defaults(func=self._teams)

    self._parsers = {
      'info': info,
      'nextround': nextRound,
      'version': version,
      'maps': maps,
      'player': player,
      'knownmaps': knownmaps,
      'teams': teams
    }

  def _serverInfo(self, args):
    rv = self._client.getServerInfo()
    d = rv.get()
    return "\n".join(["%s: %s" % (x, d[x]) for x in d])

  def _version(self, args):
    rv = self._client.getVersion()
    d = rv.get()
    return d

  def _nextRound(self, args):
    rv = self._client.nextRound()
    return rv.get()

  def _restartRound(self, args):
    rv = self._client.restartRound()
    return rv.get()

  def _maps(self, args):
    context = MapsContext(client)
    return context

  def _player(self, args):
    context = PlayerContext(client)
    return context

  def _knownMaps(self, args):
    rv = self._client.knownMaps()
    d = rv.get()
    s = ["%s (%s): %s" % (d[m]["name"], m, " ".join(d[m]["modes"])) for m in d]
    return "\n".join(s)

  def _teams(self, args):
    rv = self._client.teams()
    d = rv.get()
    s = ["%s. %s" % (k, d[k]) for k in sorted(d.keys())]
    return "\n".join(s)

class MapsContext(Context):
  _prompt = "maps"
  def __init__(self, client):
    self._client = client

    maplist = InternalParser("list", add_help=False)
    maplist.set_defaults(func=self._maplist)

    clear = InternalParser("clear", add_help=False)
    clear.set_defaults(func=self._clear)

    add = InternalParser("add", add_help=False)
    add.set_defaults(func=self._add)
    add.add_argument("name")
    add.add_argument("gamemode")
    add.add_argument("rounds")

    remove = InternalParser("remove", add_help=False)
    remove.set_defaults(fun=self._remove)
    remove.add_argument("position")

    setnext = InternalParser("setnext", add_help=False)
    setnext.set_defaults(func=self._setnext)
    setnext.add_argument("position", type=int)
    self._parsers = {'list': maplist, 'add': add, 'setnext': setnext, 'clear': clear, 'remove': remove}

  def _maplist(self, args):
    rv = self._client.listMaps()
    l = rv.get()

    v = self._client.listMapIndices().get()
    currentIndex, nextIndex = [int(x) for x in v]
    s = ""
    print "(* = Current Map, ! = Next Map)"
    for (i,k) in enumerate(l):
      prefix = " "
      if i == currentIndex:
        prefix = "*"
      elif i == nextIndex:
        prefix = "!"

      s += "%s%s. %s\t%s\t%s" % (prefix, i+1, k[0], k[1], k[2])
      s += "\n"
    return s

  def _add(self, args):
    rv = self._client.addMap(args.name, args.gamemode, args.rounds)
    return rv.get()

  def _clear(self, args):
    rv = self._client.clearMaps()
    return rv.get()

  def _setnext(self, args):
    rv = self._client.setNextMap(args.position-1)
    return rv.get()

class PlayerContext(Context):
  _prompt = "player"
  def __init__(self, client):
    self._client = client

    list = InternalParser("list", add_help=False)
    list.set_defaults(func=self._list)

    self._parsers = {'list': list }

  def _list(self, args):
    rv = self._client.listPlayers()
    return rv.get()

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
        if len(args) > 0:
          currentContext.help(args[0])
        else:
          currentContext.help()
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
