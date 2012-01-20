import os
import gevent
import binascii
import hashlib
import crypt
from gevent import event

class Control(object):
  def __init__(self, server, password, mapData, modeData):
    self.server = server
    self._mapData = mapData
    self._modeData = modeData
    self._password = password

  def getServer(self):
    return self.server

  def knownMaps(self):
    rv = event.AsyncResult()
    data = self._mapData
    rv.set(data)
    return rv

  def listTeams(self):
    rv = event.AsyncResult()
    infoRv = self.server.info()
    gevent.spawn(lambda i: self._modeData[i.get()["gameMode"]]["teams"], infoRv).link(rv)
    return rv

  def getSalt(self):
    salt = os.urandom(16)
    return binascii.hexlify(salt).upper()

  def auth(self, salt, crypt):
    g = hashlib.md5()
    g.update(binascii.unhexlify(salt) + self._password.encode("ascii"))
    golden = g.hexdigest().upper()
    return golden == crypt.upper()
