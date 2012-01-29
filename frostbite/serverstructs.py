# XXX: Replace with something sane, like actual objects, or protobufs.
class OpenStruct(object):
  def __init__(self):
    self.__dict__ = {}

  def __getattr__(self, i):
    if i in self.__dict__:
      return self.__dict__[i]
    else:
      raise AttributeError, i

  def __setattr__(self, i, v):
    if i in self.__dict__:
      self.__dict__[i] = v
    else:
      self.__dict__.update({i:v})
    return v

  def __str__(self):
    return "%s" % self.__dict__

  def dict(self):
    return self.__dict__

class ServerState(object):
  """
  Structure representing the basic state of a BF3 server.
  """
  def __init__(self, server_name, player_count, max_players, game_mode,
               map_name, current_round, total_rounds, num_teams, team_scores,
               target_scores, online_state, is_ranked, has_punkbuster, has_password,
               server_uptime, round_time, join_address, punkbuster_version, join_queue_enabled,
               region, ping_site, country):
    self.server_name = server_name
    self.player_count = player_count
    self.max_players = max_players
    self.game_mode = game_mode
    self.map_name = map_name
    self.current_round = current_round
    self.total_rounds = total_rounds
    self.num_teams = num_teams
    self.team_scores = team_scores
    self.target_scores = target_scores
    self.online_state = online_state
    self.is_ranked = is_ranked
    self.has_punkbuster = has_punkbuster
    self.has_password = has_password
    self.server_uptime = server_uptime
    self.round_time = round_time
    self.join_address = join_address
    self.punkbuster_version = punkbuster_version
    self.join_queue_enabled = join_queue_enabled
    self.region = region
    self.ping_site = ping_site
    self.country = country

  def to_dict(self):
    """
    Helper method that returns a python dictionary containing the information in this structure.
    """

    rv = {
      'server_name': self.server_name,
      'player_count': self.player_count,
      'max_players': self.max_players,
      'game_mode': self.game_mode,
      'map_name': self.map_name,
      'current_round': self.current_round,
      'total_rounds': self.total_rounds,
      'num_teams': self.num_teams,
      'team_scores': self.team_scores,
      'target_scores': self.target_scores,
      'online_state': self.online_state,
      'is_ranked': self.is_ranked,
      'has_punkbuster': self.has_punkbuster,
      'has_password': self.has_password,
      'server_uptime': self.server_uptime,
      'round_time': self.round_time,
      'join_address': self.join_address,
      'punkbuster_version': self.punkbuster_version,
      'join_queue_enabled': self.join_queue_enabled,
      'region': self.region,
      'ping_site': self.ping_site,
      'country': self.country
    }
    return rv

  @staticmethod
  def from_dict(d):
    """
    Alternative constructor that returns a ServerState structure from a python dictionary.
    """

    rv = ServerState(
      d["server_name"], d["player_count"], d["max_players"], d["game_mode"],
      d["map_name"], d["current_round"], d["total_rounds"], d["num_teams"],
      d["team_scores"], d["target_scores"],
      d["online_state"], d["is_ranked"], d["has_punkbuster"], d["has_password"],
      d["server_uptime"], d["round_time"], d["join_address"], d["punkbuster_version"],
      d["join_queue_enabled"], d["region"], d["ping_site"], d["country"])

    return rv

  def to_packet_array(self):
    """
    Helper method that returns an array of words suitable for encoding in a Frostbite packet.
    """

    rv = [self.server_name, str(self.player_count), str(self.max_players),
          self.game_mode, self.map_name, str(self.current_round),
          str(self.total_rounds), str(self.num_teams)]
    for i in self.team_scores:
      rv.append(str(i))

    rv.extend([str(self.target_scores), self.online_state, self.is_ranked, self.has_punkbuster,
               self.has_password, str(self.server_uptime), str(self.round_time), self.join_address,
               self.punkbuster_version, self.join_queue_enabled, self.region, self.ping_site,
               self.country])

    return rv

  @staticmethod
  def from_packet_array(a):
    """
    Alternative constructor that returns a ServerState structure from a list of words from a
    Frostbite packet.
    """
    serverName = a[0]
    playerCount = int(a[1])
    maxPlayers = int(a[2])
    gameMode = a[3]
    mapName = a[4]
    currentRound = int(a[5])
    totalRounds = a[6]
    numTeams = int(a[7])
    teamScores = []
    for i in range(numTeams):
      teamScores.append(int(float(a[7+i+1])))
    targetScores = int(float(a[7+numTeams+1]))
    onlineState = a[7+numTeams+2]
    isRanked = a[7+numTeams+3]
    hasPunkbuster = a[7+numTeams+4]
    hasPassword  = a[7+numTeams+5]
    serverUptime = int(a[7+numTeams+6])
    roundTime = int(a[7+numTeams+7])
    joinAddress = a[7+numTeams+8]
    punkbusterVersion = a[7+numTeams+9]
    joinQueueEnabled = a[7+numTeams+10]
    region = a[7+numTeams+11]
    pingSite = a[7+numTeams+12]
    country = a[7+numTeams+13]
    return ServerState(serverName, playerCount, maxPlayers, gameMode,
                       mapName, currentRound, totalRounds, numTeams,
                       teamScores, targetScores, onlineState, isRanked,
                       hasPunkbuster, hasPassword, serverUptime, roundTime,
                       joinAddress, punkbusterVersion, joinQueueEnabled, region,
                       pingSite, country)

class PlayerCollection(object):
  """
  Represents a collection of players and information about them. Due to the way the frostbite protocol currently
  sends this info, it also provides a list of field names that are sent alongside the player list.

  :param names: Array containing the field names
  :param players: Array of arrays of players' info blocks.
  """
  def __init__(self, names, players):
    self._names = names
    self._players = players

  def __delitem__(self, key):
    self._players.__delitem__(key)

  def __getitem__(self, item):
    return self._players.__getitem__(item)

  def __setitem__(self, key, value):
    self._players.__setitem__(key, value)

  def __len__(self):
    return len(self._players)

  def get_field_names(self):
    """
    Return the list of field names.

    :return: Array of field names.

    """
    return self._names

  def players(self):
    """
    Return the list of players' info blocks.

    :return: Array of arrays containing players' info blocks

    """
    return self._players

  @staticmethod
  def from_dict(dict):
    """
    Transforms a python dictionary of the form
    `{"fields": [field_names], "players": [[player_info_block1, player_info_block2]]}`
    into a player collection.

    :param dict: Dictionary
    :return: PlayerCollection

    """
    return PlayerCollection(dict["fields"], dict["players"])

  def to_dict(self):
    """
    Returns a python dictionary of the form
    `{"fields": [field_names], "players": [[player_info_block1, player_info_block2]]}`

    :return: dictionary

    """
    return { "fields": self.get_field_names(), "players": self.players() }

  def to_packet_array(self):
    """
    Helper method to return an array of words suitable for encoding this PlayerCollection into a packet.

    :return: list of words.

    """
    rv = [str(len(self._names))]
    rv.extend(self._names)
    rv.append(str(len(self._players)))
    for player in self._players:
      rv.extend(player)
    return rv

  @staticmethod
  def from_packet_array(a):
    """
    Alternative constructor to return a PlayerCollection from a list of words from a packet.

    :param a: Array of words from a packet returning a player info block.
    :return: PlayerCollection

    """
    num_names = int(a[0])
    field_names = a[1:1+num_names]
    num_players = int(a[1+num_names])
    players = []
    base = 1+num_names+1
    for i in range(num_players):
      player_base = base + i * num_names
      players.append(a[player_base:player_base+num_names])

    return PlayerCollection(field_names, players)

class Ban(OpenStruct):
  pass

class Map(object):
  def __init__(self, name, mode, num_rounds):
    self.name = name
    self.mode = mode
    self.num_rounds = num_rounds

  def to_dict(self):
    return {'name': self.name, 'mode': self.mode, 'num_rounds': self.num_rounds}

  @staticmethod
  def from_dict(d):
    return Map(d['name'], d['mode'], d['num_rounds'])

  def to_packet_array(self):
    return [self.name, self.mode, self.num_rounds]

  def __len__(self):
    return 3

class MapList(object):
  def __init__(self, maps):
    self.maps = maps

  def to_dict(self):
    return {'maps': [map.to_dict() for map in self.maps]}

  @staticmethod
  def from_dict(d):
    return MapList([Map.from_dict(map) for map in d["maps"]])

  def to_packet_array(self):
    # assume that all maps  have the same # of args for now
    rv = [len(self.maps), len(self.maps[0])]
    for map in self.maps:
      rv.extend(map.to_packet_array())

    return rv

  @staticmethod
  def from_packet_array(a):
    num_maps = int(a[0])
    words_per_map = int(a[1])
    rv = []
    for i in range(num_maps):
      pos = 2+(i*words_per_map)
      slice = a[pos:pos+words_per_map]
      name = slice[0]
      mode = slice[1]
      num_rounds = slice[2]
      rv.append(Map(name, mode, num_rounds))

    return MapList(rv)

