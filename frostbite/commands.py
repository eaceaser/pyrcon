from frostbite.packet import Packet

from frostbite.serverstate import ServerState

import hashlib

class FrostbiteMessage:
  def toPacket(self, seq):
    return Packet(False, False, seq, self.words)

  filter = lambda self,p,c: p

class Version(FrostbiteMessage):
  words = ["version"]
  filter = lambda self,p,c: " ".join(p.words[1:])

class ServerInfo(FrostbiteMessage):
  words = ["serverInfo"]

  def _toServerState(self, packet, c):
    serverstate = ServerState()
    serverstate.serverName = packet.words[1]
    serverstate.playerCount = int(packet.words[2])
    serverstate.maxPlayers = int(packet.words[3])
    serverstate.gameMode = packet.words[4]
    serverstate.mapName = packet.words[5]
    serverstate.currentRound = int(packet.words[6])
    serverstate.totalRounds = packet.words[7]
    serverstate.numTeams = int(packet.words[8])
    numTeams = serverstate.numTeams
    serverstate.teamScores = []
    for i in range(serverstate.numTeams):
      serverstate.teamScores.append(int(packet.words[8+i+1]))
    serverstate.targetScores = int(packet.words[8+numTeams+1])
    serverstate.onlineState = packet.words[8+numTeams+2]
    serverstate.isRanked = packet.words[8+numTeams+3]
    serverstate.hasPunkbuster = packet.words[8+numTeams+4]
    serverstate.hasPassword  = packet.words[8+numTeams+5]
    serverstate.serverUptime = int(packet.words[8+numTeams+6])
    serverstate.roundTime = int(packet.words[8+numTeams+7])
    serverstate.joinAddress = packet.words[8+numTeams+8]
    serverstate.punkbusterVersion = packet.words[8+numTeams+9]
    serverstate.joinQueueEnabled = packet.words[8+numTeams+10]
    serverstate.region = packet.words[8+numTeams+11]
    serverstate.pingSite = packet.words[8+numTeams+12]
    serverstate.country = packet.words[8+numTeams+13]
    return serverstate

  filter = _toServerState

class LoginSecret(FrostbiteMessage):
  words = ["login.hashed"]
  def __init__(self, secret):
    self.words.append(secret)

class Login(FrostbiteMessage):
  words = ["login.hashed"]

  def __init__(self, password):
    self.password = password

  def _hashPass(self, salt, password):
    m = hashlib.md5()
    decoded = salt.decode('hex')
    m.update(decoded+password.encode("ascii"))
    return m.hexdigest().upper()

  def _handleHashed(self, packet, client):
    salt = packet.words[1]
    hashed = self._hashPass(salt, self.password)
    r = client.send(LoginSecret(hashed))
    return r.get()

  filter = _handleHashed
