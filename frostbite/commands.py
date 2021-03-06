from frostbite.packet import Packet
from frostbite.serverstructs import ServerState, MapList, PlayerCollection, Ban

class FrostbiteMessage(object):
  """
  Base class for a Frostbite message structure.
  """

  def toPacket(self, seq):
    """
    Returns a packet structure that encapsulates the message.

    :param seq: Sequence number for the packet.
    :return: :mod:`frostbite.packet`
    """
    return Packet(False, False, seq, self.words)

  response = lambda self,p,c: " ".join(p.words)

class FrostbiteVariable(FrostbiteMessage):
  pass

class FrostbiteEvent(FrostbiteMessage):
  pass

class ResponsePacket(FrostbiteMessage):
  """
  Frostbite message that describes a response to another message.

  :param response_code: String response code for the message
  :param words: Response words for the message
  """

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

def define_message_type(packet_name, args = [], validate_args=None, dict=None, response=None, generator=None, base=FrostbiteMessage, doc=None):
  class_name = _packet_to_camel_case(packet_name)
  type_dict = {}
  if dict is not None:
    type_dict.update(dict)

  if doc is not None:
    type_dict["__doc__"] = doc

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

def define_event_type(packet_name, args = [], validate_args=None, dict=None, response=None, generator=None, doc=None):
  rv = define_message_type(packet_name, args, validate_args, dict, response, generator, base=FrostbiteEvent, doc=doc)
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
    for i in range(num):
      base = 2+(i*5)
      banslice = packet.words[base:base+5]
      ban = Ban.from_packet_array(banslice)
      bans.append(ban)
  return bans

def _say_generator(packet):
  message = packet.words[1]
  scope = packet.words[2]
  if scope == "all":
    return AdminSay(message=message, scope="all")
  elif scope == "team":
    team_id = packet.words[3]
    return AdminSay(message=message, scope="team", team=team_id)
  else:
    raise Exception

def _list_players_generator(packet):
  scope = packet.words[1]
  if scope == "all":
    return AdminListPlayers(scope="all")
  elif scope == "team":
    team_id = packet.words[2]
    return AdminListPlayers(scope="team", team=team_id)
  else:
    raise Exception

define_message_type("version", response=lambda s,p,c: " ".join(p.words[1:]), doc="Asks for the server's version.")
define_message_type("serverInfo", response=lambda s,p,c:ServerState.from_packet_array(p.words[1:]), doc="Asks for basic info from the server.")
define_message_type("login.hashed", args=["password"], response=lambda s,p,c: p.words[1] if len(p.words) > 1 else p.words[0], doc="Begins or ends a hashed login sequence.")
define_event_type("player.onAuthenticated", args=["name"], doc="Event raised when a player authenticates to the server.")
define_event_type("player.onJoin", args=["name", "guid"], doc="Event raised when a player joins the server.")
define_event_type("player.onLeave", args=["name", "info"], doc="Event raised when a player leaves the server.")
define_event_type("player.onSpawn", args=["name", "team"], doc="Event raised when a player spawns.")
define_event_type("player.onKill", args=["killer", "killed", "weapon", "headshot"], doc="Event raised when a player is killed.")
define_event_type("player.onChat", args=["name", "text"], doc="Event raised when a player or the server sends a message.")
define_event_type("player.onSquadChange", args=["name", "team", "squad"], doc="Event raised when a player changes squads.")
define_event_type("player.onTeamChange", args=["name", "team", "squad"], doc="Event raised when a player changes teams.")
define_event_type("punkBuster.onMessage", args=["message"], doc="Event raised when PunkBuster emits a message.")
define_event_type("server.onLevelLoaded", args=["name", "gamemode", "rounds_played", "rounds_total"], doc="Event raised when the server loads a new level.")
define_event_type("server.onRoundOver", args=["winning_team"], doc="Event raised when the server ends a round.")
define_event_type("server.onRoundOverPlayers", args=["players"], doc="Event raised when the server ends a round, containing player info.")
define_event_type("server.onRoundOverTeamScores", args=["team_scores"], doc="Event raised when the server ends a round, containing team scores.")
define_message_type("admin.eventsEnabled", args=["enable"], doc="Asks the server to begin sending events.")
define_message_type("admin.say", args=["message", "scope", "team", "squad", "player"], validate_args=_validate_say_args, generator=_say_generator, doc="Write a message to the in game chat.")
define_message_type("admin.listPlayers", args=["scope", "team"], response=_parse_players_list, validate_args=_validate_list_players, generator=_list_players_generator, doc="List current players.")
define_message_type("logout", doc="Logout from the server's RCon")
define_message_type("quit", doc="Quit from the server.")
define_message_type("punkBuster.isActive", doc="Asks the server if punkbuster is active.")
define_message_type("punkBuster.activate", doc="Asks the server to activate punkbuster.")
define_message_type("punkBuster.pb_sv_command", args=["command"], doc="Asks the server to relay a command to punkbuster.")
define_message_type("admin.kickPlayer", args=["player_name", "reason"], doc="Ask the server to kick a player.")
define_message_type("admin.movePlayer", args=["player_name", "team_id", "squad_id", "force_kill"], doc="Asks the server to move a player.")
define_message_type("admin.killPlayer", args=["player_name"], doc="Asks the server to kill a player.")
define_message_type("gameAdmin.load", doc="Asks the server to load the admin list from disk.")
define_message_type("gameAdmin.save", doc="Asks the server to save the admin list to disk.")
define_message_type("gameAdmin.add", args=["player", "level"], doc="Add a player to the admin list.")
define_message_type("gameAdmin.remove", args=["player"], doc="Asks th server to remove a player from the admin list.")
define_message_type("gameAdmin.list", doc="Asks the server to list the known admins.")
define_message_type("banList.load", doc="Asks the server to load the ban list from disk.")
define_message_type("banList.save", doc="Asks the server to save the ban list from disk.")
define_message_type("banList.add", args=["id_type", "id", "timeout", "reason"], doc="Asks the server to add someone to the ban list.")
define_message_type("banList.remove", args=["id_type", "id"], doc="Asks the server to remove someone from the ban list.")
define_message_type("banList.clear", doc="Asks the server to clear the banlist.")
define_message_type("banList.list", args=["offset"], response=_parse_ban_list, doc="Asks the server for the ban list.")
define_message_type("reservedSlotsList.load", doc="Asks the server to load the reserved slots list from disk.")
define_message_type("reservedSlotsList.save", doc="Asks the server to save the reserved slots list to disk.")
define_message_type("reservedSlotsList.add", args=["name"], doc="Asks the server to add someone to the reserved slots list.")
define_message_type("reservedSlotsList.remove", args=["name"], doc="Asks the server to remove someone from the reserved slots list.")
define_message_type("reservedSlotsList.clear", doc="Clears the reserved slotslist.")
define_message_type("reservedSlotsList.list", doc="Asks the server to list the reserved slots.")
define_message_type("mapList.load", doc="Asks the server to load the map list from disk.")
define_message_type("mapList.save", doc="Asks the server to save the map list to disk.")
define_message_type("mapList.add", args=["map_name", "gamemode", "rounds", "index"], doc="Asks the server to add a map to the map list.")
define_message_type("mapList.remove", args=["index"], doc="Asks the server to delete a map from the map list.")
define_message_type("mapList.clear", doc="Asks the server to clear the map list.")
define_message_type("mapList.list", response=lambda s,p,c: MapList.from_packet_array(p.words[1:]), doc="Asks the server to list the map list.")
define_message_type("mapList.setNextMapIndex", args=["index"], doc="Asks the server to set the next map to the specified index in the map list.")
define_message_type("mapList.getMapIndices", response=lambda s,p,c: [p.words[1], p.words[2]], doc="Asks the server for the current and next map indices")
define_message_type("mapList.runNextRound", doc="Asks the server to run the next round immediately.")
define_message_type("mapList.restartRound", doc="Asks the server to restart the round immediately.")
define_message_type("mapList.endRound", args=["winning_team"], doc="Asks the server to end the current round immediately.")

define_variable_type("vars.ranked")
define_variable_type("vars.serverName")
define_variable_type("vars.gamePassword")
define_variable_type("vars.autoBalance")
define_variable_type("vars.friendlyFire")
define_variable_type("vars.maxPlayers")
define_variable_type("vars.killCam")
define_variable_type("vars.killRotation")
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
