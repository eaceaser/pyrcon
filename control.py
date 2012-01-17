from gevent import event

class Control(object):
  def __init__(self, server, mapData, modeData):
    self._server = server
    self._mapData = mapData
    self._modeData = modeData

  def getServer(self):
    return self._server

  def knownMaps(self):
    rv = event.AsyncResult()
    data = self._mapData
    rv.set(data)
    return rv
