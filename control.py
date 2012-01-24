from frostbite import crypt

import gevent
from gevent import event

class Control(object):
  def __init__(self, server, password, mapData, modeData):
    self.server = server
    self._mapData = mapData
    self._modeData = modeData
    self._password = password

  def getServer(self):
    return self.server

  def known_maps(self):
    rv = event.AsyncResult()
    data = self._mapData
    rv.set(data)
    return rv

  def list_teams(self):
    rv = event.AsyncResult()
    infoRv = self.server.info()
    gevent.spawn(lambda i: self._modeData[i.get()["gameMode"]]["teams"], infoRv).link(rv)
    return rv

  def get_salt(self):
    return crypt.get_salt()

  def auth(self, salt, pw):
    return crypt.auth(salt, self._password, pw)
