class Control:
  def __init__(self):
    self._servers = {}

  def addServer(self, name, server):
    self._servers[name] = server

  def getServerIds(self):
    return self._servers.keys()

  def hasServerId(self, name):
    return name in self._servers

  def getServer(self, name):
    return self._servers[name]

  def getServerInfo(self, name):
    info = self._servers[name].info().dict()
    return info
