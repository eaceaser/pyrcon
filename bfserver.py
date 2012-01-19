from frostbite import client, commands

import gevent
from gevent import event

# class which contains stateful knowledge of a BF3 Server
class BFServer(object):
  def __init__(self, host, port, password):
    self._host = host
    self._port = port
    self._password = password
    self._client = None
    self._loggedIn = False
    self._mapListLoaded = False
    self._handlers = []

    self._attemptConnect()
    self._login()
    self._enable_events()

  def _login(self):
    assert self._hasClient()
    login = commands.Login(self._password)
    loginResponse = self._client.send(login)
    # NOTE: blocks until ware logged in
    loginResponse.get()
    self._loggedIn = True
    self._event_handlers = []

  def _hasClient(self):
    return self._client is not None

  def _isLoggedIn(self):
    return self._loggedIn is True

  def _mapListIsLoaded(self):
    return self._mapListLoaded is True

  def _attemptConnect(self):
    self._client = client.FBClient(self._host, self._port, self._dispatch_event)
    self._client.start()

  def _dispatch_event(self, command):
    if isinstance(command, commands.PlayerOnAuthenticated):
      for handler in self._handlers:
        gevent.spawn(lambda h,c: h.on_player_authenticated(c.name), handler, command)
    elif isinstance(command, commands.PlayerOnJoin):
      for handler in self._handlers:
        gevent.spawn(lambda h,c: h.on_player_join(c.name, c.guid), handler, command)
    elif isinstance(command, commands.PlayerOnLeave):
      for handler in self._handlers:
        gevent.spawn(lambda h,c: h.on_player_leave(c.name, c.info), handler, command)
    elif isinstance(command, commands.PlayerOnSpawn):
      for handler in self._handlers:
        gevent.spawn(lambda h,c: h.on_player_spawn(c.name, c.team), handler, command)
    elif isinstance(command, commands.PlayerOnKill):
      for handler in self._handlers:
        gevent.spawn(lambda h,c: h.on_player_kill(c.killer, c.killed, c.weapon, c.headshot), handler, command)
    elif isinstance(command, commands.PlayerOnChat):
      for handler in self._handlers:
        gevent.spawn(lambda h,c: h.on_player_chat(c.name, c.text), handler, command)
    elif isinstance(command, commands.PlayerOnSquadChange):
      for handler in self._handlers:
        gevent.spawn(lambda h,c: h.on_player_squad_change(c.name, c.team, c.squad), handler, command)
    elif isinstance(command, commands.PlayerOnTeamChange):
      for handler in self._handlers:
        gevent.spawn(lambda h,c: h.on_player_team_change(c.name, c.team, c.squad), handler, command)
    elif isinstance(command, commands.PunkBusterOnMessage):
      for handler in self._handlers:
        gevent.spawn(lambda h,c: h.on_punkbuster_message(c.message), handler, command)
    elif isinstance(command, commands.ServerOnLevelLoaded):
      for handler in self._handlers:
        gevent.spawn(lambda h,c: h.on_level_loaded(c.name, c.gamemode, c.rounds_played, c.rounds_total), handler, command)
    elif isinstance(command, commands.ServerOnRoundOver):
      for handler in self._handlers:
        gevent.spawn(lambda h,c: h.on_round_over(c.winning_team), handler, command)
    elif isinstance(command, commands.OnRoundOverTeamScores):
      for handler in self._handlers:
        gevent.spawn(lambda h,c: h.on_round_over_team_scores(c.team_scores), handler, command)

  def _respondToLoadedMapList(self):
    self._mapListLoaded = True

  def _loadMapList(self):
    assert self._hasClient()
    assert self._isLoggedIn()
    msg = commands.MapListLoad()
    rv = self._client.send(msg)
    rv.rawlink(lambda d: self._respondToLoadedMapList())

  def _enable_events(self):
    assert self._hasClient()
    assert self._isLoggedIn()
    msg = commands.AdminEventsEnabled(True)
    rv = self._client.send(msg)
    rv.get()

  def add_event_handler(self, handler):
    self._handlers.append(handler)

  def info(self):
    assert self._client is not None
    serverInfo = commands.ServerInfo()
    innerrv = self._client.send(serverInfo)
    rv = event.AsyncResult()
    gevent.spawn(lambda: innerrv.get().dict()).link(rv)
    return rv

  def version(self):
    assert self._client is not None
    version = commands.Version()
    resp = self._client.send(version)
    return resp

  def nextRound(self):
    cmd = commands.MapListRunNextRound()
    return self._client.send(cmd)

  def restartRound(self):
    cmd = commands.MapListRestartRound()
    return self._client.send(cmd)

  def listMaps(self):
    assert self._isLoggedIn()
    cmd = commands.MapListList()
    innerrv = self._client.send(cmd)
    rv = event.AsyncResult()
    gevent.spawn(lambda r: map(lambda i: [i.name, i.gamemode, i.rounds], r.get()), innerrv).link(rv)
    return rv

  def getMapIndices(self):
    assert self._isLoggedIn()
    cmd = commands.MapListGetMapIndices()
    return self._client.send(cmd)

  def addMap(self, name, gamemode, rounds):
    assert self._isLoggedIn()
    cmd = commands.MapListAdd(name, gamemode, rounds)
    rv = self._client.send(cmd)
    return rv

  def setNextMap(self, index):
    assert self._isLoggedIn()
    cmd = commands.MapListSetNextMapIndex(index)
    rv = self._client.send(cmd)
    return rv

  def clearMapList(self):
    assert self._isLoggedIn()
    cmd = commands.MapListClear()
    rv = self._client.send(cmd)
    return rv

  def saveMapList(self):
    assert self._isLoggedIn()
    cmd = commands.MapListSave()
    rv = self._client.send(cmd)
    return rv

  def removeMap(self, index):
    assert self._isLoggedIn()
    cmd = commands.MapListRemove(index)
    rv = self._client.send(cmd)
    return rv

  def listPlayers(self):
    assert self._isLoggedIn()
    cmd = commands.AdminListAllPlayers()
    innerrv = self._client.send(cmd)
    rv = event.AsyncResult()
    gevent.spawn(lambda r: map(lambda p: [p.name], r.get()), innerrv).link(rv)
    return rv

  def kickPlayer(self, playerName, reason=None):
    assert self._isLoggedIn()
    cmd = commands.AdminKickPlayer(playerName, reason)
    rv = self._client.send(cmd)
    return rv

  def killPlayer(self, playerName):
    assert self._isLoggedIn()
    cmd = commands.AdminKillPlayer(playerName)
    rv = self._client.send(cmd)
    return rv

  def listBans(self):
    assert self._isLoggedIn()
    cmd = commands.BanListList()
    struct_rv = self._client.send(cmd)
    rv = event.AsyncResult()
    gevent.spawn(lambda r: [[b.id, b.idType, b.banType, b.time, b.reason] for b in r.get()], struct_rv).link(rv)
    return rv

  def say_all(self, msg):
    assert self._isLoggedIn()
    cmd = commands.AdminSay(msg)
    rv = self._client.send(cmd)
    return rv
