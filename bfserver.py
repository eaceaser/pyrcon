from frostbite import crypt, client, commands

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
    salt_command = commands.LoginHashed()
    salt_response = self._client.send(salt_command)
    salt = salt_response.get()

    login_command = commands.LoginHashed(password=crypt.hash_pass(salt, self._password))
    loginResponse = self._client.send(login_command)
    response = loginResponse.get()
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

  def _dispatch_event(self, client, seq, command):
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
    elif isinstance(command, commands.ServerOnRoundOverPlayers):
      for handler in self._handlers:
        gevent.spawn(lambda h,c: h.on_round_over_players(c.players), handler, command)
    elif isinstance(command, commands.ServerOnRoundOverTeamScores):
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
    msg = commands.AdminEventsEnabled(enable=True)
    rv = self._client.send(msg)
    rv.get()

  def add_event_handler(self, handler):
    self._handlers.append(handler)

  def info(self):
    assert self._client is not None
    serverInfo = commands.ServerInfo()
    inner_rv = self._client.send(serverInfo)
    rv = event.AsyncResult()
    gevent.spawn(lambda: inner_rv.get().to_dict()).link(rv)
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
    inner_rv = self._client.send(cmd)
    rv = event.AsyncResult()
    gevent.spawn(lambda r: map(lambda i: [i.name, i.gamemode, i.rounds], r.get()), inner_rv).link(rv)
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
    cmd = commands.AdminListPlayers(scope="all")
    innerrv = self._client.send(cmd)
    rv = event.AsyncResult()
    gevent.spawn(lambda r: r.get().to_dict(), innerrv).link(rv)
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

  def list_variables(self):
    assert self._isLoggedIn()
    outer_rv = event.AsyncResult()
    rvs = []
    for var_type in commands.variable_types.values():
      var = var_type(None)
      var_rv = event.AsyncResult()
      rv = self._client.send(var)
      gevent.spawn(lambda v,r: [v.words[0], r.get()], var, rv).link(var_rv)
      rvs.append(var_rv)

    gevent.spawn(lambda rs: dict([p.get() for p in rs]), rvs).link(outer_rv)
    return outer_rv

  def set_variable(self, key, val):
    assert self._isLoggedIn()
    variable = commands.variable_types[key](val)
    rv = self._client.send(variable)
    return rv

  def get_variable(self, key):
    assert self._isLoggedIn()
    variable = commands.variable_types[key]()
    rv = self._client.send(variable)
    return rv
