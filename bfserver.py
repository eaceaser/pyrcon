from frostbite import client, commands

import gevent
from gevent import event

# class which contains stateful knowledge of a BF3 Server
class BFServer(object):
  def _hasClient(self):
    return self._client is not None

  def _isLoggedIn(self):
    return self._loggedIn is True

  def _mapListIsLoaded(self):
    return self._mapListLoaded is True

  def _attemptConnect(self):
    self._client = client.FBClient(self._host, self._port)
    self._client.start()

  def _login(self):
    assert self._hasClient()
    login = commands.Login(self._password)
    loginResponse = self._client.send(login)
    # NOTE: blocks until ware logged in
    loginResponse.get()
    self._loggedIn = True

  def _respondToLoadedMapList(self):
    self._mapListLoaded = True

  def _loadMapList(self):
    assert self._hasClient()
    assert self._isLoggedIn()
    msg = commands.MapListLoad()
    rv = self._client.send(msg)
    rv.rawlink(lambda d: self._respondToLoadedMapList())

  def __init__(self, host, port, password):
    self._host = host
    self._port = port
    self._password = password
    self._client = None
    self._loggedIn = False
    self._mapListLoaded = False

    self._attemptConnect()
    self._login()
#    self._loadMapList()

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
