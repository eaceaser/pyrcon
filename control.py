import os
import gevent
import binascii
import hashlib
import crypt
from gevent import event

class Control(object):
  def __init__(self, server, password, mapData, modeData):
    self._server = server
    self._mapData = mapData
    self._modeData = modeData
    self._password = password

  def getServer(self):
    return self._server

  def knownMaps(self):
    rv = event.AsyncResult()
    data = self._mapData
    rv.set(data)
    return rv

  def listTeams(self):
    rv = event.AsyncResult()
    infoRv = self._server.info()
    gevent.spawn(lambda i: self._modeData[i.get()["gameMode"]]["teams"], infoRv).link(rv)
    return rv

  def getSalt(self):
    salt = os.urandom(32)
    return binascii.hexlify(salt)

  def auth(self, salt, crypt):
    m = hashlib.md5()
    m.update(salt)
    m.update(crypt)
    test = m.digest()

    g = hashlib.md5()
    g.update(salt)
    g.update(self._password)
    golden = m.digest()

    return golden == test
