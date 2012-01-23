from frostbite.packet import Packet
from frostbite.serverstructs import ServerState, Map, PlayerCollection, Ban

class FrostbiteMessage(object):
  def toPacket(self, seq):
    return Packet(False, False, seq, self.words)

  response = lambda self,p,c: " ".join(p.words)

class FrostbiteVariable(FrostbiteMessage):
  pass

class FrostbiteEvent(FrostbiteMessage):
  pass

class ResponsePacket(FrostbiteMessage):
  def __init__(self, response_code, *words):
    self.words = [response_code]
    self.words.extend(words)

  def toPacket(self, seq):
    return Packet(False, True, seq, self.words)

event_types = {}
event_generators = {}

message_types = {}
message_generators = {}

variable_types = {}
variable_generators = {}

def _packet_to_camel_case(packet_name):
  parts = packet_name.split(".")
  new_parts = []
  for s in parts:
    new_str = s[0].upper() + s[1:]
    new_parts.append(new_str)

  class_name = "".join(new_parts)
  return class_name

def define_message_type(packet_name, args = [], validate_args=None, dict=None, response=None, generator=None, base=FrostbiteMessage):
  class_name = _packet_to_camel_case(packet_name)
  type_dict = {}
  if dict is not None:
    type_dict.update(dict)

  if response is not None:
    type_dict['response'] = response

  for arg in args:
    type_dict[arg] = None

  def init(self, **kwargs):
    self.words = [packet_name]

    if validate_args is not None:
      validate_args(**kwargs)

    for arg in args:
      value = kwargs.get(arg, None)
      if value is not None:
        self.words.append(value)
      setattr(self, arg, value)

    FrostbiteMessage.__init__(self)

  type_dict['__init__'] = init
  rv = type(class_name, (base,), type_dict)

  def generator_func(packet):
    if generator is not None:
      return generator(packet)
    else:
      kwargs = {}
      if len(packet.words) > 1:
        for i, arg in enumerate(args):
          kwargs[arg] = packet.words[i+1]
      return rv(**kwargs)

  message_types[packet_name] = rv
  message_generators[packet_name] = generator_func
  globals()[class_name] = rv

def define_event_type(packet_name, args = [], validate_args=None, dict=None, response=None, generator=None):
  rv = define_message_type(packet_name, args, validate_args, dict, response, generator, base=FrostbiteEvent)
  event_types[packet_name] = rv
  event_generators[packet_name] = message_generators[packet_name]
  return rv

def define_variable_type(variable_name):
  class_name = _packet_to_camel_case(variable_name)
  response = lambda s,p,c: p.words[1] if len(p.words) > 1 else p.words[0]
  type_dict = {'words': [variable_name], 'response': response}
  def init(self, value=None):
    if value is not None:
      setattr(self, "value", value)
      self.words.append(value)

    FrostbiteMessage.__init__(self)

  type_dict['__init__'] = init
  rv = type(class_name, (FrostbiteVariable,), type_dict)

  def generator(packet):
    value = None
    if len(packet.words) > 1:
      value = packet.words[1]

    return rv(value)

  message_types[variable_name] = rv
  message_generators[variable_name] = generator
  variable_types[variable_name] = rv
  variable_generators[variable_name] = generator
  globals()[class_name] = rv

def _validate_say_args(**kwargs):
  if kwargs["scope"] == "all":
    if kwargs.has_key("team") or kwargs.has_key("squad") or kwargs.has_key("player"):
      raise Exception
  elif kwargs["scope"] == "team":
    if kwargs.has_key("squad") or kwargs.has_key("player") or not kwargs.has_key("team"):
      raise Exception
  elif kwargs["scope"] == "player":
    if kwargs.has_key("squad") or kwargs.has_key("team") or not kwargs.has_key("player"):
      raise Exception
  elif kwargs["scope"] == "squad":
    if kwargs.has_key("player") or not (kwargs.has_key["team"] and kwargs.has_key["squad"]):
      raise Exception
  else:
    raise Exception

def _validate_list_players(**kwargs):
  if kwargs["scope"] == "all":
    if kwargs.has_key("team"):
      raise Exception
  elif kwargs["scope"] == "team":
    if not kwargs.has_key("team"):
      raise Exception

def _parse_players_list(self, packet, client):
  return PlayerCollection.from_packet_array(packet.words[1:])

def _parse_ban_list(self, packet, client):
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
      pos += 5
  return bans

def _parse_map_list(self, packet, client):
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

def _list_players_generator(packet):
  scope = packet.words[1]
  if scope == "all":
    return AdminListPlayers(scope="all")
  elif scope == "team":
    team_id = packet.words[2]
    return AdminListPlayers(scope="team", team=team_id)
  else:
    raise Exception

define_message_type("version", response=lambda s,p,c: " ".join(p.words[1:]))
define_message_type("serverInfo", response=lambda s,p,c:ServerState.from_packet_array(p.words[1:]))
define_message_type("login.hashed", args=["password"], response=lambda s,p,c: p.words[1] if len(p.words) > 1 else p.words[0])
define_event_type("player.onAuthenticated", args=["name"])
define_event_type("player.onJoin", args=["name", "guid"])
define_event_type("player.onLeave", args=["name", "info"])
define_event_type("player.onSpawn", args=["name", "team"])
define_event_type("player.onKill", args=["killer", "killed", "weapon", "headshot"])
define_event_type("player.onChat", args=["name", "text"])
define_event_type("player.onSquadChange", args=["name", "team", "squad"])
define_event_type("player.onTeamChange", args=["name", "team", "squad"])
define_event_type("punkBuster.onMessage", args=["message"])
define_event_type("server.onLevelLoaded", args=["name", "gamemode", "rounds_played", "rounds_total"])
define_event_type("server.onRoundOver", args=["winning_team"])
define_event_type("server.onRoundOverPlayers", args=["players"])
define_event_type("server.onRoundOverTeamScores", args=["team_scores"])
define_message_type("admin.eventsEnabled", args=["enable"])
define_message_type("admin.adminSay", args=["message", "scope", "team", "squad", "player"], validate_args=_validate_say_args)
define_message_type("admin.listPlayers", args=["scope", "team"], response=_parse_players_list, validate_args=_validate_list_players, generator=_list_players_generator)
define_message_type("logout")
define_message_type("quit")
define_message_type("punkBuster.isActive")
define_message_type("punkBuster.activate")
define_message_type("admin.kickPlayer", args=["player_name", "reason"])
define_message_type("admin.movePlayer", args=["player_name", "team_id", "squad_id", "force_kill"])
define_message_type("admin.killPlayer", args=["player_name"])
define_message_type("banList.load")
define_message_type("banList.save")
define_message_type("banList.add", args=["id_type", "id", "timeout", "reason"])
define_message_type("banList.remove", args=["id_type", "id"])
define_message_type("banList.clear")
define_message_type("banList.list", args=["offset"], response=_parse_ban_list)
define_message_type("mapList.load")
define_message_type("mapList.save")
define_message_type("mapList.add", args=["map_name", "gamemode", "rounds", "index"])
define_message_type("mapList.remove", args=["index"])
define_message_type("mapList.clear")
define_message_type("mapList.list", response=_parse_map_list)
define_message_type("mapList.setNextMapIndex", args=["index"])
define_message_type("mapList.getMapIndices", response=lambda s,p,c: [p.words[1], p.words[2]])
define_message_type("mapList.runNextRound")
define_message_type("mapList.restartRound")
define_message_type("mapList.endRound", args=["winning_team"])

define_variable_type("vars.ranked")
define_variable_type("vars.serverName")
define_variable_type("vars.gamePassword")
define_variable_type("vars.autoBalance")
define_variable_type("vars.friendlyFire")
define_variable_type("vars.maxPlayers")
define_variable_type("vars.killCam")
define_variable_type("vars.miniMap")
define_variable_type("vars.hud")
define_variable_type("vars.crossHair")
define_variable_type("vars.3dSpotting")
define_variable_type("vars.miniMapSpotting")
define_variable_type("vars.nameTag")
define_variable_type("vars.3pCam")
define_variable_type("vars.regenerateHealth")
define_variable_type("vars.teamKillCountForKick")
define_variable_type("vars.teamKillValueIncrease")
define_variable_type("vars.teamKillKickForBan")
define_variable_type("vars.idleTimeout")
define_variable_type("vars.idleBanRounds")
define_variable_type("vars.roundStartPlayerCount")
define_variable_type("vars.roundRestartPlayerCount")
define_variable_type("vars.vehicleSpawnAllowed")
define_variable_type("vars.vehicleSpawnDelay")
define_variable_type("vars.soldierHealth")
define_variable_type("vars.playerRespawnTime")
define_variable_type("vars.playerManDownTime")
define_variable_type("vars.bulletDamage")
define_variable_type("vars.gameModeCounter")
define_variable_type("vars.onlySquadLeaderSpawn")
define_variable_type("vars.unlockMode")
