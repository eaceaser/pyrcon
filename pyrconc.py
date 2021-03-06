#!/usr/bin/env python

import os
import readline
import argparse
import json
import hashlib
import binascii
import atexit

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
  def __init__(self, hostname, port, password):
    self._socket = None
    self._hostname = hostname
    self._port = port
    self._password = password
    self._send_queue = gevent.queue.Queue()
    self._read_queue = gevent.queue.Queue()
    self._group = gevent.pool.Group()

  def _connect(self):
    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    address = (socket.gethostbyname(self._hostname), self._port)
    self._socket.connect(address)

  def start(self):
    self._connect()
    self._group.spawn(self._send_loop)
    self._auth()

  def _auth(self):
    fileobj = self._socket.makefile()
    saltmsg = json.loads(fileobj.readline().rstrip())
    salt = saltmsg["salt"]
    md5 = hashlib.md5()
    md5.update(salt.decode("hex"))
    md5.update(self._password.encode("ascii"))
    rv = md5.hexdigest()
    resp = {"secret": rv.upper()}
    fileobj.write(json.dumps(resp))
    fileobj.write("\n")
    fileobj.flush()

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

      if response == None or response == "":
        print "Connection lost. Reconnecting."
        self._socket = None
        self._connect()
        self._auth()
        fileobj = self._socket.makefile()
        rv.set("")
        continue

      jsonResponse = json.loads(response)
      rv.set(jsonResponse["response"])

  def nextRound(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "next_round" }
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
    j = { "server": True, "methodName": "restart_round" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def listMaps(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "list_maps" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def listMapIndices(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "get_map_indices"}
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def addMap(self, name, gamemode, rounds):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "add_map" }
    j["arguments"] = [name, gamemode, rounds]
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def removeMap(self, index):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "remove_map", "arguments": [index] }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def saveMaps(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "save_map_list" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def knownMaps(self):
    rv = event.AsyncResult()
    j = { "server": False, "methodName": "known_maps" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def setNextMap(self, position):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "set_next_map", "arguments": [position] }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def clearMaps(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "clear_map_list" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def listPlayers(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "list_all_players" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def teams(self):
    rv = event.AsyncResult()
    j = { "server": False, "methodName": "list_teams" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def kickPlayer(self, player, reason=None):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "kick_player" }
    args = [ player ]
    if reason is not None:
      args.append(reason)
    j["arguments"] = args
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def killPlayer(self, player):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "kill_player", "arguments": [ player ] }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def listBans(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "list_bans" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def listVars(self):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "list_variables" }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

  def setVar(self, key, value):
    rv = event.AsyncResult()
    j = { "server": True, "methodName": "set_variable", "arguments": [key, value] }
    s = json.dumps(j)
    self._send_queue.put((s, rv))
    return rv

class Context(object):
  def __init__(self):
    self.set_completer()

  def set_completer(self):
    readline.set_completer(lambda t,n: [s for s in self._parsers
                                        if s.startswith(t)][n])

  def help(self, cmd=None):
    if cmd is None:
      for i in self._parsers:
        self._parsers[i].print_usage()
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

    ban = InternalParser('ban', description="Ban List Context", add_help=False)
    ban.set_defaults(func=self._ban)

    vars = InternalParser('vars', description="Server Variables Context", add_help=False)
    vars.set_defaults(func=self._vars)

    self._parsers = {
      'info': info,
      'nextround': nextRound,
      'version': version,
      'maps': maps,
      'player': player,
      'ban': ban,
      'knownmaps': knownmaps,
      'teams': teams,
      'vars': vars
    }

    Context.__init__(self)

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

  def _ban(self, args):
    context = BanContext(client)
    return context

  def _vars(self, args):
    context = VarsContext(client)
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
    remove.add_argument("position", type=int)

    setnext = InternalParser("setnext", add_help=False)
    setnext.set_defaults(func=self._setnext)
    setnext.add_argument("position", type=int)

    save = InternalParser("save", add_help=False)
    save.set_defaults(func=self._save)

    self._parsers = {
      'list': maplist,
      'add': add,
      'setnext': setnext,
      'clear': clear,
      'remove': remove,
      'save': save
     }

    Context.__init__(self)

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

  def _remove(self, args):
    rv = self._client.removeMap(args.position-1)
    return rv.get()

  def _save(self, args):
    rv = self._client.saveMaps()
    return rv.get()

class PlayerContext(Context):
  _prompt = "player"
  def __init__(self, client):
    self._client = client

    list = InternalParser("list", add_help=False)
    list.set_defaults(func=self._list)

    kick = InternalParser("kick", add_help=False)
    kick.set_defaults(func=self._kick)
    kick.add_argument("player")
    kick.add_argument("-r", "--reason", required=False)

    kill = InternalParser("kill", add_help=False)
    kill.set_defaults(func=self._kill)
    kill.add_argument("player")

    self._parsers = {
      'list': list,
      'kick': kick,
      'kill': kill
    }

    Context.__init__(self)

  def _list(self, args):
    rv = self._client.listPlayers()
    return rv.get()

  def _kick(self, args):
    rv = self._client.kickPlayer(args.player, args.reason)
    return rv.get()

  def _kill(self, args):
    rv = self._client.killPlayer(args.player)
    return rv.get()

class BanContext(Context):
  _prompt = "ban"

  def __init__(self, client):
    self._client = client

    list = InternalParser("list", add_help=False)
    list.set_defaults(func = self._list)

    add = InternalParser("add", add_help=False)
    add.add_argument("id_type")
    add.add_argument("id")
    add.add_argument("ban_type")
    add.add_argument("time")
    add.add_argument("--reason", "-r")
    add.set_defaults(func = self._add)

    self._parsers = {
      'list': list
    }

    Context.__init__(self)

  def _list(self, args):
    rv = self._client.listBans()
    bans = rv.get()
    formatted = ["%s (%s) - %s (%s) - %s" % (b[0], b[1], b[2], b[3], b[4]) for b in bans]
    return "\n".join(formatted)

class VarsContext(Context):
  _prompt = "vars"

  def __init__(self, client):
    self._client = client

    list = InternalParser("list", add_help=False)
    list.set_defaults(func=self._list)
    set = InternalParser("set", add_help=False)
    set.add_argument("name")
    set.add_argument("value")
    set.set_defaults(func=self._set)

    self._parsers = {
      'set': set,
      'list': list
    }

    Context.__init__(self)

  def _list(self, args):
    rv = self._client.listVars()
    vars = rv.get()
    formatted = ["%s: %s" % (v, vars[v]) for v in vars]
    return "\n".join(formatted)

  def _set(self, args):
    name = args.name
    value = args.value
    rv = self._client.setVar(name, value)
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
        self._contexts[-1].set_completer()
      else:
        rv = currentContext.execute(cmd, args)
        if type(rv) == str or type(rv) == unicode:
          print rv
        elif isinstance(rv, Context):
          self._contexts.append(rv)

parser = argparse.ArgumentParser(description='Command line client for PyRCon.')
parser.add_argument('--host', '-H', dest='host', help='PyRCon Hostname', default="localhost")
parser.add_argument('--port', '-p', dest='port', help='PyRCon Port', type=int, default=31337)
parser.add_argument('--password', '-P', dest='password', help='Server Password', required=True)
args = parser.parse_args()

client = SimpleJsonClient(args.host, args.port, args.password)
client.start()
histfile = os.path.join(os.path.expanduser("~"), ".pyrconchist")
readline.parse_and_bind("tab: complete")
try:
  readline.read_history_file(histfile)
except IOError:
  pass
atexit.register(readline.write_history_file, histfile)
g = Console(client)
g.start()
g.join()
