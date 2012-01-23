from frostbite.packet import Packet

from frostbite.serverstructs import ServerState, Map, PlayerCollection, Ban

import binascii
import hashlib

#TODO: Metaprogram this file.

class FrostbiteMessage(object):
  def toPacket(self, seq):
    return Packet(False, False, seq, self.words)

  filter = lambda self,p,c: p.words[0]

class ResponsePacket(FrostbiteMessage):
  def __init__(self, response_code, *words):
    self.words = [response_code]
    self.words.extend(words)

  def toPacket(self, seq):
    return Packet(False, True, seq, self.words)

class Version(FrostbiteMessage):
  words = ["version"]
  filter = lambda self,p,c: " ".join(p.words[1:])

  @staticmethod
  def fromPacket(packet):
    return Version()

class ServerInfo(FrostbiteMessage):
  words = ["serverInfo"]

  def _toServerState(self, packet, c):
    return ServerState.from_packet_array(packet.words[1:])

  filter = _toServerState

  @staticmethod
  def fromPacket(packet):
    return ServerInfo()

class LoginRequest(FrostbiteMessage):
  def __init__(self):
    self.words = ["login.hashed"]

class LoginSecret(FrostbiteMessage):
  def __init__(self, secret):
    self.words = ["login.hashed"]
    self.words.append(secret)
    self.secret = secret

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

  @staticmethod
  def fromPacket(packet):
    if len(packet.words) > 1 and packet.isResponse == False:
      return LoginSecret(packet.words[1])
    elif len(packet.words) > 1 and packet.isResponse == True:
      return Login(packet.words[1])
    else:
      return LoginRequest()

# Events
class PlayerOnAuthenticated(FrostbiteMessage):
  def __init__(self, name):
    self.words = [ "player.onAuthenticated" ]
    self.words.append(name)
    self.name = name

  @staticmethod
  def fromPacket(packet):
    return PlayerOnAuthenticated(packet.words[1])

class PlayerOnJoin(FrostbiteMessage):
  def __init__(self, name, guid):
    self.words = [ "player.onJoin" ]
    self.words.extend([name, guid])
    self.name = name
    self.guid = guid

  @staticmethod
  def fromPacket(packet):
    return PlayerOnJoin(*packet.words[1:])

class PlayerOnLeave(FrostbiteMessage):
  def __init__(self, name, info):
    self.words = [ "player.onLeave" ]
    self.words.extend([name, info])
    self.name = name
    self.info = info

  @staticmethod
  
  def fromPacket(packet):
    name = packet.words[1]
    collection = PlayerCollection.from_packet_array(packet.words[2:])
    return PlayerOnLeave(name, collection)

class PlayerOnSpawn(FrostbiteMessage):
  def __init__(self, name, team):
    self.words = [ "player.onSpawn" ]
    self.words.extend([name, team])
    self.name = name
    self.team = team

  @staticmethod
  def fromPacket(packet):
    return PlayerOnSpawn(*packet.words[1:])

class PlayerOnKill(FrostbiteMessage):
  def __init__(self, killer, killed, weapon, headshot):
    self.words = [ "player.onKill" ]
    self.words.extend([killer, killed, weapon, headshot])
    self.killer = killer
    self.killed = killed
    self.weapon = weapon
    self.headshot = headshot

  @staticmethod
  def fromPacket(packet):
    return PlayerOnKill(*packet.words[1:])

class PlayerOnChat(FrostbiteMessage):
  def __init__(self, name, text):
    self.words = [ "player.onChat" ]
    self.words.extend([name, text])
    self.name = name
    self.text = text

  @staticmethod
  def fromPacket(packet):
    return PlayerOnChat(*packet.words[1:])

class PlayerOnSquadChange(FrostbiteMessage):
  def __init__(self, name, team, squad):
    self.words = [ "player.onSquadChange" ]
    self.words.extend([name, team, squad])
    self.name = name
    self.team = team
    self.squad = squad

  @staticmethod
  def fromPacket(packet):
    return PlayerOnSquadChange(*packet.words[1:])

class PlayerOnTeamChange(FrostbiteMessage):
  def __init__(self, name, team, squad):
    self.words = [ "player.onTeamChange" ]
    self.words.extend([name, team, squad])
    self.name = name
    self.team = team
    self.squad = squad

  @staticmethod
  def fromPacket(packet):
    return PlayerOnTeamChange(*packet.words[1:])

class PunkBusterOnMessage(FrostbiteMessage):
  def __init__(self, message):
    self.words = [ "punkBuster.onMessage" ]
    self.words.append(message)
    self.message = message

  @staticmethod
  def fromPacket(packet):
    return PunkBusterOnMessage(packet.words[1])

class ServerOnLevelLoaded(FrostbiteMessage):
  def __init__(self, name, gamemode, rounds_played, rounds_total):
    self.words = [ "server.onLevelLoaded" ]
    self.words.extend([name, gamemode, rounds_played, rounds_total])
    self.name = name
    self.gamemode = gamemode
    self.rounds_played = rounds_played
    self.rounds_total = rounds_total

  @staticmethod
  def fromPacket(packet):
    return ServerOnLevelLoaded(*packet.words[1:])

class ServerOnRoundOver(FrostbiteMessage):
  def __init__(self, winning_team):
    self.words = ["server.onRoundOver"]
    self.words.append(winning_team)
    self.winning_team = winning_team

  @staticmethod
  def fromPacket(packet):
    return ServerOnRoundOver(packet.words[1:])

class ServerOnRoundOverPlayers(FrostbiteMessage):
  def __init__(self, players):
    self.words = ["server.onRoundOverPlayers"]
    self.players = players
  
  @staticmethod
  def fromPacket(packet):
    info = PlayerCollection.from_packet_array(packet.words[1:])
    return ServerOnRoundOverPlayers(info)

class ServerOnRoundOverTeamScores(FrostbiteMessage):
  def __init__(self, team_scores):
    self.words = ["server.onRoundOverTeamScores"]
    self.words.append(team_scores)
    self.team_scores = team_scores

  @staticmethod
  def fromPacket(packet):
    return ServerOnRoundOverTeamScores(packet.words[1])

events = {
  u"player.onAuthenticated": PlayerOnAuthenticated.fromPacket,
  u"player.onJoin": PlayerOnJoin.fromPacket,
  u"player.onLeave": PlayerOnLeave.fromPacket,
  u"player.onSpawn": PlayerOnSpawn.fromPacket,
  u"player.onKill": PlayerOnKill.fromPacket,
  u"player.onChat": PlayerOnChat.fromPacket,
  u"player.onSquadChange": PlayerOnSquadChange.fromPacket,
  u"player.onTeamChange": PlayerOnTeamChange.fromPacket,
  u"punkBuster.onMessage": PunkBusterOnMessage.fromPacket,
  u"server.onLevelLoaded": ServerOnLevelLoaded.fromPacket,
  u"server.onRoundOver": ServerOnRoundOver.fromPacket,
  u"server.onRoundOverTeamScores": ServerOnRoundOverTeamScores.fromPacket,
  u"server.onRoundOverPlayers": ServerOnRoundOverPlayers.fromPacket
}

# Commands
class AdminEventsEnabled(FrostbiteMessage):
  def __init__(self, enable = True):
    self.words = ["admin.eventsEnabled"]
    if enable:
      self.words.append("true")
    else:
      self.words.append("false")

  @staticmethod
  def fromPacket(packet):
    return AdminEventsEnabled(packet.words[1])

class AdminSay(FrostbiteMessage):
  def __init__(self, message):
    self.words = ["admin.say"]
    self.words.extend([message, "all"])

  @staticmethod
  def fromPacket(packet):
    return AdminSay(packet.words[1])

class AdminSayTeam(FrostbiteMessage):
  def __init__(self, message, teamId):
    self.words = ["admin.say"]
    self.words.extend([message, "team", teamId])

  @staticmethod
  def fromPacket(packet):
    return AdminSayTeam(*packet.words[1:])

class AdminSaySquad(FrostbiteMessage):
  def __init__(self, message, teamId, squadId):
    self.words = ["admin.say"]
    self.words.extend([message, "squad", teamId, squadId])

  @staticmethod
  def fromPacket(packet):
    return AdminSaySquad(*packet.words[1:])

class AdminSayPlayer(FrostbiteMessage):
  def __init__(self, message, playerName):
    self.words = ["admin.say"]
    self.words.extend([message, "player", playerName])

  @staticmethod
  def fromPacket(packet):
    return AdminSayPlayer(*packet.words[1:])

class AdminListPlayers(FrostbiteMessage):
  def _handlePlayerList(self, packet, client):
    return PlayerCollection.from_packet_array(packet.words[1:])
  filter = _handlePlayerList

  @staticmethod
  def fromPacket(packet):
    sub_method = packet.words[1]
    if sub_method == "all":
      return AdminListAllPlayers()
    elif sub_method == "team":
      return AdminListTeamPlayers(packet.words[2])

class AdminListAllPlayers(AdminListPlayers):
  def __init__(self):
    self.words = ["admin.listPlayers", "all"]

  @staticmethod
  def fromPacket(packet):
    return AdminListAllPlayers()

class AdminListTeamPlayers(AdminListPlayers):
  def __init__(self, teamNum):
    self.words = ["admin.listPlayers", "team"]
    self.words.append(teamNum)

  @staticmethod
  def fromPacket(packet):
    return AdminListTeamPlayers(packet.words[1])

class Logout(FrostbiteMessage):
  def __init__(self):
    self.words = ["logout"]

  @staticmethod
  def fromPacket(packet):
    return Logout()

class Quit(FrostbiteMessage):
  def __init__(self):
    self.words = ["quit"]

  @staticmethod
  def fromPacket(packet):
    return Quit()

# punkbuster commands
class PunkBusterActive(FrostbiteMessage):
  def __init__(self):
    self.words = ["punkBuster.isActive"]
  filter = lambda s,p,c: p.words[1]

  @staticmethod
  def fromPacket(packet):
    return PunkBusterActive()

class PunkBusterActivate(FrostbiteMessage):
  def __init__(self):
    self.words = ["punkBuster.activate"]

  @staticmethod
  def fromPacket(packet):
    return PunkBusterActivate()

# player commands
class AdminKickPlayer(FrostbiteMessage):
  def __init__(self, playerName, reason = None):
    self.words = ["admin.kickPlayer"]
    self.words.append(playerName)
    if reason is not None: self.words.append(reason)

  @staticmethod
  def fromPacket(packet):
    return AdminKickPlayer(*packet.words[1:])

class AdminMovePlayer(FrostbiteMessage):
  def __init__(self, playerName, teamId, squadId, forceKill):
    self.words = ["admin.movePlayer"]
    self.words.extend([playerName, teamId, squadId, forceKill])

  @staticmethod
  def fromPacket(packet):
    return AdminMovePlayer(*packet.words[1:])

class AdminKillPlayer(FrostbiteMessage):
  def __init__(self, playerName):
    self.words = ["admin.killPlayer"]
    self.words.append(playerName)

  @staticmethod
  def fromPacket(packet):
    return AdminKillPlayer(packet.words[1])

# ban commands
class BanListLoad(FrostbiteMessage):
  def __init__(self):
    self.words = ["banList.load"]

  @staticmethod
  def fromPacket(packet):
    return BanListLoad()

class BanListSave(FrostbiteMessage):
  def __init__(self):
    self.words = ["banList.save"]

  @staticmethod
  def fromPacket(packet):
    return BanListSave()

class BanListAdd(FrostbiteMessage):
  def __init__(self, idType, idVal, timeout, reason = None):
    self.words = ["banList.add"]
    self.words.extend([idType, idVal, timeout])
    if reason is not None: self.words.append(reason)

  @staticmethod
  def fromPacket(packet):
    return BanListAdd(*packet.words[1:])

class BanListRemove(FrostbiteMessage):
  def __init__(self, idType, idVal):
    self.words = ["banList.remove"]
    self.words.extend([idType, idVal])

  @staticmethod
  def fromPacket(packet):
    return BanListRemove(*packet.words[1:])

class BanListClear(FrostbiteMessage):
  def __init__(self):
    self.words = ["banList.clear"]

  @staticmethod
  def fromPacket(packet):
    return BanListClear()

class BanListList(FrostbiteMessage):
  def __init__(self, offset = None):
    self.words = ["banList.list"]
    if offset is not None: self.words.append(offset)

  def _parseBanList(self, packet, client):
    bans = []
    if len(packet.words) > 1:
      num = int(packet.words[1])
      pos = 2
      for i in range(num):
        banslice = packet.words[pos:pos+5]
        ban = Ban()
        ban.idType = banslice[0]
        ban.id = banslice[1]
        ban.banType = banslice[2]
        ban.time = banslice[3]
        ban.reason = banslice[4]
        bans.append(ban)
        pos = pos+5
    return bans

  filter = _parseBanList

  @staticmethod
  def fromPacket(packet):
    return BanListList(*packet.words[1])

# map list commands
class MapListLoad(FrostbiteMessage):
  def __init__(self):
    self.words = ["mapList.load"]

  @staticmethod
  def fromPacket(packet):
    return MapListLoad()

class MapListSave(FrostbiteMessage):
  def __init__(self):
    self.words = ["mapList.save"]

  @staticmethod
  def fromPacket(packet):
    return MapListSave()

class MapListAdd(FrostbiteMessage):
  def __init__(self, mapName, gamemode, rounds, index = None):
    self.words = ["mapList.add"]
    self.words.extend([mapName, gamemode, str(rounds)])

  @staticmethod
  def fromPacket(packet):
    return MapListAdd(*packet.words[1:])

class MapListRemove(FrostbiteMessage):
  def __init__(self, index):
    self.words = ["mapList.remove"]
    self.words.append(str(index))

  @staticmethod
  def fromPacket(packet):
    return MapListRemove(packet.words[1])

class MapListClear(FrostbiteMessage):
  def __init__(self):
    self.words = ["mapList.clear"]

  @staticmethod
  def fromPacket(packet):
    return MapListClear()

class MapListList(FrostbiteMessage):
  def __init__(self):
    self.words = ["mapList.list"]

  def _parseMapList(self, packet, client):
    numMaps = int(packet.words[1])
    wordsPerMap = int(packet.words[2])
    pos = 3
    maps = []
    for i in range(numMaps):
      mapslice = packet.words[pos:pos+wordsPerMap]
      pos += wordsPerMap
      map = Map()
      map.name = mapslice[0]
      map.gamemode = mapslice[1]
      map.rounds = mapslice[2]
      maps.append(map)

    return maps
  filter = _parseMapList

  @staticmethod
  def fromPacket(packet):
    return MapListList()

class MapListSetNextMapIndex(FrostbiteMessage):
  def __init__(self, index):
    self.words = ["mapList.setNextMapIndex"]
    self.words.append(str(index))

  @staticmethod
  def fromPacket(packet):
    return MapListSetNextMapIndex(packet.words[1])

class MapListGetMapIndices(FrostbiteMessage):
  def __init__(self):
    self.words = ["mapList.getMapIndices"]

  filter = lambda s,p,c: [p.words[1], p.words[2]]

  @staticmethod
  def fromPacket(packet):
    return MapListGetMapIndices()

class MapListGetRounds(FrostbiteMessage):
  def __init__(self, index):
    self.words = ["mapList.getRounds"]

  filter = lambda s,p,c: [p.words[1], p.words[2]]
  @staticmethod
  def fromPacket(packet):
    return MapListGetRounds()

class MapListRunNextRound(FrostbiteMessage):
  def __init__(self):
    self.words = ["mapList.runNextRound"]

  @staticmethod
  def fromPacket(packet):
    return MapListRunNextRound()

class MapListRestartRound(FrostbiteMessage):
  def __init__(self):
    self.words = ["mapList.restartRound"]

  @staticmethod
  def fromPacket(packet):
    return MapListRestartRound()

class MapListEndRound(FrostbiteMessage):
  def __init__(self, winningTeamId):
    self.words = ["mapList.endRound"]
    self.words.append(winningTeamId)

  @staticmethod
  def fromPacket(packet):
    return MapListEndRound(packet.words[1])

# class MapListAvailableMaps(FrostbiteMessage)

# Server variables

commands = {
  u'login.hashed': Login.fromPacket,
  u'version': Version.fromPacket,
  u'serverInfo': ServerInfo.fromPacket,
  u'admin.eventsEnabled': AdminEventsEnabled.fromPacket,
  u'admin.say': AdminSay.fromPacket,
  u'admin.listPlayers': AdminListPlayers.fromPacket,
  u'logout': Logout.fromPacket,
  u'quit': Quit.fromPacket,
  u'punkBuster.isActive': PunkBusterActive.fromPacket,
  u'punkBuster.activate': PunkBusterActivate.fromPacket,
  u'admin.kickPlayer': AdminKickPlayer.fromPacket,
  u'admin.movePlayer': AdminMovePlayer.fromPacket,
  u'admin.killPlayer': AdminKillPlayer.fromPacket,
  u'banList.load': BanListLoad.fromPacket,
  u'banList.save': BanListSave.fromPacket,
  u'banList.add': BanListAdd.fromPacket,
  u'banList.remove': BanListRemove.fromPacket,
  u'banList.clear': BanListClear.fromPacket,
  u'mapList.load': MapListLoad.fromPacket,
  u'mapList.save': MapListSave.fromPacket,
  u'mapList.add': MapListAdd.fromPacket,
  u'mapList.remove': MapListRemove.fromPacket,
  u'mapList.clear': MapListClear.fromPacket,
  u'mapList.list': MapListList.fromPacket,
  u'mapList.setNextMapIndex': MapListSetNextMapIndex.fromPacket,
  u'mapList.getMapIndices': MapListGetMapIndices.fromPacket,
  u'mapList.getRounds': MapListGetRounds.fromPacket,
  u'mapList.runNextRound': MapListRunNextRound.fromPacket,
  u'mapList.restartRound': MapListRestartRound.fromPacket,
  u'mapList.endRound': MapListEndRound.fromPacket
}

# Variables
class FrostbiteVariable(FrostbiteMessage):
  def __init__(self, value):
    if value is not None:
      self.words.append(value)

  @staticmethod
  def fromPacket(packet):
    value = None
    print packet.words
    if len(packet.words) > 1:
      value = packet.words[1]
    return FrostbiteVariable.__init__(value)

  def _parse_variable(self, packet, client):
    if len(packet.words) > 1:
      return packet.words[1]
    else:
      return packet.words[0]

  filter = _parse_variable

class VarsRanked(FrostbiteVariable):
  def __init__(self, value = None):
    self.words = [ "vars.ranked" ]
    self.name = "ranked"
    FrostbiteVariable.__init__(self, value)

class VarsServerName(FrostbiteVariable):
  def __init__(self, value = None):
    self.words = ["vars.serverName"]
    self.name = "serverName"
    FrostbiteVariable.__init__(self, value)

class VarsGamePassword(FrostbiteVariable):
  def __init__(self, value = None):
    self.words = [ "vars.gamePassword" ]
    self.name = "gamePassword"
    FrostbiteVariable.__init__(self, value)

class VarsAutoBalance(FrostbiteVariable):
  def __init__(self, value = None):
    self.words = [ "vars.autoBalance" ]
    FrostbiteVariable.__init__(self, value)

class VarsFriendlyFire(FrostbiteVariable):
  def __init__(self, value = None):
    self.words = [ "vars.friendlyFire" ]
    FrostbiteVariable.__init__(self, value)

class VarsMaxPlayers(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.maxPlayers"]
    FrostbiteVariable.__init__(self, value)

class VarsKillCam(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.killCam"]
    FrostbiteVariable.__init__(self, value)

class VarsMiniMap(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.miniMap"]
    FrostbiteVariable.__init__(self, value)

class VarsHud(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.hud"]
    FrostbiteVariable.__init__(self, value)

class VarsCrossHair(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.crossHair"]
    FrostbiteVariable.__init__(self, value)

class Vars3dSpotting(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.3dSpotting"]
    FrostbiteVariable.__init__(self, value)

class VarsMiniMapSpotting(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = [ "vars.miniMapSpotting" ]
    FrostbiteVariable.__init__(self, value)

class VarsNameTag(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = [ "vars.nameTag" ]
    FrostbiteVariable.__init__(self, value)

class Vars3pCam(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.3pCam"]
    FrostbiteVariable.__init__(self, value)

class VarsRegenerateHealth(FrostbiteVariable):
  def __init__(self, value = None):
    self.words = ["vars.regenerateHealth"]
    FrostbiteVariable.__init__(self, value)

class VarsTeamKillCountForKick(FrostbiteVariable):
  def __init__(self, value = None):
    self.words = ["vars.teamKillCountForKick"]
    FrostbiteVariable.__init__(self, value)

class VarsTeamKillValueIncrease(FrostbiteVariable):
  def __init__(self, value = None):
    self.words = ["vars.teamKillValueIncrease"]
    FrostbiteVariable.__init__(self, value)

class VarsTeamKillValueDecreasePerSecond(FrostbiteVariable):
  def __init__(self, value = None):
    self.words=["vars.teamKillValueDecreasePerSecond"]
    FrostbiteVariable.__init__(self, value)

class VarsTeamKillKickForBan(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.teamKillKickForBan"]
    FrostbiteVariable.__init__(self, value)

class VarsIdleTimeout(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.idleTimeout"]
    FrostbiteVariable.__init__(self, value)

class VarsIdleBanRounds(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.idleBanRounds"]
    FrostbiteVariable.__init__(self, value)

class VarsRoundStartPlayerCount(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = [ "vars.roundStartPlayerCount" ]
    FrostbiteVariable.__init__(self, value)

class VarsRoundRestartPlayerCount(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.roundRestartPlayerCount"]
    FrostbiteVariable.__init__(self, value)

class VarsVehicleSpawnAllowed(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = [ "vars.vehicleSpawnAllowed" ]
    FrostbiteVariable.__init__(self, value)

class VarsVehicleSpawnDelay(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.vehicleSpawnDelay"]
    FrostbiteVariable.__init__(self, value)

class VarsSoldierHealth(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.soldierHealth"]
    FrostbiteVariable.__init__(self, value)

class VarsPlayerRespawnTime(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.playerRespawnTime"]
    FrostbiteVariable.__init__(self, value)

class VarsPlayerManDownTime(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.playerManDownTime"]
    FrostbiteVariable.__init__(self, value)

class VarsBulletDamage(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = [ "vars.bulletDamage" ]
    FrostbiteVariable.__init__(self, value)

class VarsGameModeCounter(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.gameModeCounter"]
    FrostbiteVariable.__init__(self, value)

class VarsOnlySquadLeaderSpawn(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.onlySquadLeaderSpawn"]
    FrostbiteVariable.__init__(self, value)

class VarsUnlockMode(FrostbiteVariable):
  def __init__(self, value=None):
    self.words = ["vars.unlockMode"]
    FrostbiteVariable.__init__(self, value)

variables = {
  u'vars.ranked': VarsRanked.fromPacket,
  u'vars.serverName': VarsServerName.fromPacket,
  u'vars.gamePassword': VarsGamePassword.fromPacket,
  u'vars.autoBalance': VarsAutoBalance.fromPacket,
  u'vars.friendlyFire': VarsFriendlyFire.fromPacket,
  u'vars.maxPlayers': VarsMaxPlayers.fromPacket,
  u'vars.killCam': VarsKillCam.fromPacket,
  u'vars.miniMap': VarsMiniMap.fromPacket,
  u'vars.hud': VarsHud.fromPacket,
  u'vars.crossHair': VarsCrossHair.fromPacket,
  u'vars.3dSpotting': Vars3dSpotting.fromPacket,
  u'vars.miniMapSpotting': VarsMiniMapSpotting.fromPacket,
  u'vars.regenerateHealth': VarsRegenerateHealth.fromPacket,
  u'vars.teamKillCountForKick': VarsTeamKillCountForKick.fromPacket,
  u'vars.teamKillValueIncrease': VarsTeamKillValueIncrease.fromPacket,
  u'vars.teamKillValueDecreasePerSecond': VarsTeamKillValueDecreasePerSecond.fromPacket,
  u'vars.teamKillKickForBan': VarsTeamKillKickForBan.fromPacket,
  u'vars.idleTimeout': VarsIdleTimeout.fromPacket,
  u'vars.idleBanRounds': VarsIdleBanRounds.fromPacket,
  u'vars.roundStartPlayerCount': VarsRoundStartPlayerCount.fromPacket,
  u'vars.roundRestartPlayerCount': VarsRoundRestartPlayerCount.fromPacket,
  u'vars.vehicleSpawnAllowed': VarsVehicleSpawnAllowed.fromPacket,
  u'vars.vehicleSpawnDelay': VarsVehicleSpawnDelay.fromPacket,
  u'vars.soldierHealth': VarsSoldierHealth.fromPacket,
  u'vars.playerRespawnTime': VarsPlayerRespawnTime.fromPacket,
  u'vars.playerManDownTime': VarsPlayerManDownTime.fromPacket,
  u'vars.bulletDamage': VarsBulletDamage.fromPacket,
  u'vars.gameModeCounter': VarsGameModeCounter.fromPacket,
  u'vars.onlySquadLeaderSpawn': VarsOnlySquadLeaderSpawn.fromPacket,
  u'vars.unlockMode': VarsUnlockMode.fromPacket
}

variable_types = {
  u'vars.ranked': VarsRanked,
  u'vars.serverName': VarsServerName,
  u'vars.gamePassword': VarsGamePassword,
  u'vars.autoBalance': VarsAutoBalance,
  u'vars.friendlyFire': VarsFriendlyFire,
  u'vars.maxPlayers': VarsMaxPlayers,
  u'vars.killCam': VarsKillCam,
  u'vars.miniMap': VarsMiniMap,
  u'vars.hud': VarsHud,
  u'vars.crossHair': VarsCrossHair,
  u'vars.3dSpotting': Vars3dSpotting,
  u'vars.miniMapSpotting': VarsMiniMapSpotting,
  u'vars.regenerateHealth': VarsRegenerateHealth,
  u'vars.teamKillCountForKick': VarsTeamKillCountForKick,
  u'vars.teamKillValueIncrease': VarsTeamKillValueIncrease,
  u'vars.teamKillValueDecreasePerSecond': VarsTeamKillValueDecreasePerSecond,
  u'vars.teamKillKickForBan': VarsTeamKillKickForBan,
  u'vars.idleTimeout': VarsIdleTimeout,
  u'vars.idleBanRounds': VarsIdleBanRounds,
  u'vars.roundStartPlayerCount': VarsRoundStartPlayerCount,
  u'vars.roundRestartPlayerCount': VarsRoundRestartPlayerCount,
  u'vars.vehicleSpawnAllowed': VarsVehicleSpawnAllowed,
  u'vars.vehicleSpawnDelay': VarsVehicleSpawnDelay,
  u'vars.soldierHealth': VarsSoldierHealth,
  u'vars.playerRespawnTime': VarsPlayerRespawnTime,
  u'vars.playerManDownTime': VarsPlayerManDownTime,
  u'vars.bulletDamage': VarsBulletDamage,
  u'vars.gameModeCounter': VarsGameModeCounter,
  u'vars.onlySquadLeaderSpawn': VarsOnlySquadLeaderSpawn,
  u'vars.unlockMode': VarsUnlockMode
}
