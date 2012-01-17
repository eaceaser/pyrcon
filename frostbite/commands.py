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

class AdminSay(FrostbiteMessage):
  words = ["admin.say"]
  def __init__(self, message):
    self.words.extend([message, "all"])

class AdminSayTeam(FrostbiteMessage):
  words = ["admin.say"]
  def __init__(self, message, teamId):
    self.words.extend([message, "team", teamId])

class AdminSaySquad(FrostbiteMessage):
  words = ["admin.say"]
  def __init__(self, message, teamId):
    self.words.extend([message, "squad", teamId, squadId])

class AdminSayPlayer(FrostbiteMessage):
  words = ["admin.say"]
  def __init__(self, message, teamId):
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
  words = ["admin.listPlayers", "all"]

class AdminListTeamPlayers(AdminListPlayers):
  words = ["admin.listPlayers", "team"]
  def __init__(self, teamNum):
    self.words.append(teamNum)

class Logout(FrostbiteMessage):
  words = ["logout"]

class Quit(FrostbiteMessage):
  words = ["quit"]

# punkbuster commands
class PunkBusterActive(FrostbiteMessage):
  words = ["punkBuster.isActive"]
  filter = lambda s,p,c: p.words[1]

class PunkBusterActivate(FrostbiteMessage):
  words = ["punkBuster.activate"]

# player commands
class AdminKickPlayer(FrostbiteMessage):
  words = ["admin.kickPlayer"]
  def __init__(self, playerName, reason = None):
    words.append(playerName)
    if reason is not None: words.append(reason)

class AdminMovePlayer(FrostbiteMessage):
  words = ["admin.movePlayer"]
  def __init__(self, playerName, teamId, squadId, forceKill):
    words.extend([playerName, teamId, squadId, forceKill])

class AdminKillPlayer(FrostbiteMessage):
  words = ["admin.killPlayer"]
  def __init__(self, playerName):
    words.append(playerName)

# ban commands
class BanListLoad(FrostbiteMessage):
  words = ["banList.load"]

class BanListSave(FrostbiteMessage):
  words = ["banList.save"]

class BanListAdd(FrostbiteMessage):
  words = ["banList.add"]
  def __init__(self, idType, idVal, timeout, reason = None):
    words.extend([idType, idVal, timeout])
    if reason is not None: words.append(reason)

class BanListRemove(FrostbiteMessage):
  words = ["banList.remove"]
  def __init__(self, idType, idVal):
    words.extend([idType, idVal])

class BanListClear(FrostbiteMessage):
  words = ["banList.clear"]

class BanListList(FrostbiteMessage):
  words = ["banList.list"]
  def __init__(self, offset = None):
    if offset is not None: words.append(offset)

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
  words = ["mapList.load"]

class MapListSave(FrostbiteMessage):
  words = ["mapList.save"]

class MapListAdd(FrostbiteMessage):
  words = ["mapList.add"]
  def __init__(self, mapName, gamemode, rounds, index = None):
    self.words.extend([mapName, gamemode, rounds])

class MapListRemove(FrostbiteMessage):
  words = ["mapList.remove"]
  def __init__(self, index):
    words.append(index)

class MapListClear(FrostbiteMessage):
  words = ["mapList.clear"]

class MapListList(FrostbiteMessage):
  words = ["mapList.list"]
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
  words = ["mapList.setNextMapIndex"]
  def __init__(self, index):
    words.append(index)

class MapListGetMapIndicies(FrostbiteMessage):
  words = ["mapList.getMapIndices"]
  filter = lambda s,p,c: [p.words[1], p.words[2]]

class MapListGetRounds(FrostbiteMessage):
  words = ["mapList.getRounds"]
  filter = lambda s,p,c: [p.words[1], p.words[2]]

class MapListRunNextRound(FrostbiteMessage):
  words = ["mapList.runNextRound"]

class MapListRestartRound(FrostbiteMessage):
  words = ["mapList.restartRound"]

class MapListEndRound(FrostbiteMessage):
  words = ["mapList.endRound"]
  def __init__(self, winningTeamId):
    words.append(winningTeamId)

# class MapListAvailableMaps(FrostbiteMessage)

# Server variables
