from frostbite.packet import Packet

from frostbite.serverstructs import ServerState, Map, Player, Ban

import hashlib

class FrostbiteMessage(object):
  def toPacket(self, seq):
    return Packet(False, False, seq, self.words)

  filter = lambda self,p,c: p.words[0]

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
  def __init__(self, secret):
    self.words = ["login.hashed"]
    self.words.append(secret)

class Login(FrostbiteMessage):
  def __init__(self, password):
    self.words = ["login.hashed"]
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

class AdminSay(FrostbiteMessage):
  def __init__(self, message):
    self.words = ["admin.say"]
    self.words.extend([message, "all"])

class AdminSayTeam(FrostbiteMessage):
  def __init__(self, message, teamId):
    self.words = ["admin.say"]
    self.words.extend([message, "team", teamId])

class AdminSaySquad(FrostbiteMessage):
  def __init__(self, message, teamId):
    words = ["admin.say"]
    self.words.extend([message, "squad", teamId, squadId])

class AdminSayPlayer(FrostbiteMessage):
  def __init__(self, message, teamId):
    words = ["admin.say"]
    self.words.extend([message, "player", playerName])

class AdminListPlayers(FrostbiteMessage):
  def _handlePlayerList(self, packet, client):
    numParams = int(packet.words[1])
    fieldNames = packet.words[2:2+numParams]
    numPlayers = int(packet.words[2+numParams])
    base = 2+numParams+1
    players = []
    for i in range(numPlayers):
      playerFields = packet.words[base:base+numParams]
      base = base + numParams
      player = Player()
      for idx,val in enumerate(playerFields):
        player[fieldNames[idx]] = val
      players.append(player)
    return players
  filter = _handlePlayerList

class AdminListAllPlayers(AdminListPlayers):
  def __init__(self):
    self.words = ["admin.listPlayers", "all"]

class AdminListTeamPlayers(AdminListPlayers):
  def __init__(self, teamNum):
    self.words = ["admin.listPlayers", "team"]
    self.words.append(teamNum)

class Logout(FrostbiteMessage):
  def __init__(self):
    self.words = ["logout"]

class Quit(FrostbiteMessage):
  def __init__(self):
    self.words = ["quit"]

# punkbuster commands
class PunkBusterActive(FrostbiteMessage):
  def __init__(self):
    self.words = ["punkBuster.isActive"]
  filter = lambda s,p,c: p.words[1]

class PunkBusterActivate(FrostbiteMessage):
  def __init__(self):
    self.words = ["punkBuster.activate"]

# player commands
class AdminKickPlayer(FrostbiteMessage):
  def __init__(self, playerName, reason = None):
    self.words = ["admin.kickPlayer"]
    self.words.append(playerName)
    if reason is not None: self.words.append(reason)

class AdminMovePlayer(FrostbiteMessage):
  def __init__(self, playerName, teamId, squadId, forceKill):
    self.words = ["admin.movePlayer"]
    self.words.extend([playerName, teamId, squadId, forceKill])

class AdminKillPlayer(FrostbiteMessage):
  def __init__(self, playerName):
    self.words = ["admin.killPlayer"]
    self.words.append(playerName)

# ban commands
class BanListLoad(FrostbiteMessage):
  def __init__(self):
    self.words = ["banList.load"]

class BanListSave(FrostbiteMessage):
  def __init__(self):
    self.words = ["banList.save"]

class BanListAdd(FrostbiteMessage):
  def __init__(self, idType, idVal, timeout, reason = None):
    self.words = ["banList.add"]
    self.words.extend([idType, idVal, timeout])
    if reason is not None: self.words.append(reason)

class BanListRemove(FrostbiteMessage):
  def __init__(self, idType, idVal):
    self.words = ["banList.remove"]
    self.words.extend([idType, idVal])

class BanListClear(FrostbiteMessage):
  def __init__(self):
    self.words = ["banList.clear"]

class BanListList(FrostbiteMessage):
  def __init__(self, offset = None):
    self.words = ["banList.list"]
    if offset is not None: self.words.append(offset)

  def _parseBanList(self, packet, client):
    num = int(packet.words[1])
    pos = 2
    bans = []
    for i in range(num):
      banslice = packet.words[pos:pos+5]
      ban = Ban()
      ban["idType"] = banslice[0]
      ban["id"] = banslice[1]
      ban["banType"] = banslice[2]
      ban["time"] = banslice[3]
      ban["reason"] = banslice[4]
      bans.append(ban)
      pos = pos+5

    return bans

  filter = _parseBanList

# map list commands
class MapListLoad(FrostbiteMessage):
  def __init__(self):
    self.words = ["mapList.load"]

class MapListSave(FrostbiteMessage):
  def __init__(self):
    self.words = ["mapList.save"]

class MapListAdd(FrostbiteMessage):
  def __init__(self, mapName, gamemode, rounds, index = None):
    self.words = ["mapList.add"]
    self.words.extend([mapName, gamemode, rounds])

class MapListRemove(FrostbiteMessage):
  def __init__(self, index):
    self.words = ["mapList.remove"]
    self.words.append(index)

class MapListClear(FrostbiteMessage):
  def __init__(self):
    self.words = ["mapList.clear"]

class MapListList(FrostbiteMessage):
  def __init__(self):
    self.words = ["mapList.list"]

  def _parseMapList(self, packet, client):
    numMaps = int(packet.words[1])
    wordsPerMap = packet.words[2]
    pos = 3
    maps = []
    for i in range(numMaps):
      mapslice = packet.words[pos:pos+wordsPerMap]
      pos = pos + wordsPerMap
      map = Map()
      map.name = mapslice[0]
      map.gamemode = mapslice[1]
      map.rounds = mapslice[2]
      maps.append(map)

    return maps
  filter = _parseMapList

class MapListSetNextMapIndex(FrostbiteMessage):
  def __init__(self, index):
    self.words = ["mapList.setNextMapIndex"]
    self.words.append(index)

class MapListGetMapIndicies(FrostbiteMessage):
  def __init__(self, index):
    self.words = ["mapList.getMapIndices"]

  filter = lambda s,p,c: [p.words[1], p.words[2]]

class MapListGetRounds(FrostbiteMessage):
  def __init__(self, index):
    self.words = ["mapList.getRounds"]

  filter = lambda s,p,c: [p.words[1], p.words[2]]

class MapListRunNextRound(FrostbiteMessage):
  def __init__(self):
    self.words = ["mapList.runNextRound"]

class MapListRestartRound(FrostbiteMessage):
  def __init__(self):
    self.words = ["mapList.restartRound"]

class MapListEndRound(FrostbiteMessage):
  def __init__(self, winningTeamId):
    self.words = ["mapList.endRound"]
    self.words.append(winningTeamId)

# class MapListAvailableMaps(FrostbiteMessage)

# Server variables
