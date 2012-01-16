from frostbite import client, commands

# class which contains stateful knowledge of a BF3 Server
class BFServer:
  def _hasClient(self):
    return self._client is not None

  def _isLoggedIn(self):
    return self._loggedIn is True

  def _attemptConnect(self):
    self._client = client.FBClient(self._host, self._port)
    self._client.start()

  def _getServerState(self):
    assert self._client is not None
    version = commands.Version()
    serverInfo = commands.ServerInfo()

    versionResponse = self._client.send(version)
    serverInfoResponse = self._client.send(serverInfo)

    self._version = versionResponse.get()
    self._serverInfo = serverInfoResponse.get()

  def _login(self):
    assert self._hasClient()
    login = commands.Login(self._password)
    loginResponse = self._client.send(login)
    loginResponse.get()
    self._loggedIn = True

  def __init__(self, host, port, password):
    self._host = host
    self._port = port
    self._password = password
    self._client = None

    self._version = None
    self._serverInfo = None

    self._loggedIn = False

    self._attemptConnect()
    self._getServerState()
    self._login()
