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
    rv = ServerState(
      d["server_name"], d["player_count"], d["max_players"], d["game_mode"],
      d["map_name"], d["current_round"], d["total_rounds"], d["num_teams"],
      d["team_scores"], d["target_scores"],
      d["online_state"], d["is_ranked"], d["has_punkbuster"], d["has_password"],
      d["server_uptime"], d["round_time"], d["join_address"], d["punkbuster_version"],
      d["join_queue_enabled"], d["region"], d["ping_site"], d["country"])

    return rv

  def to_packet_array(self):
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
    return self._names

  def players(self):
    return self._players

  @staticmethod
  def from_dict(dict):
    return PlayerCollection(dict["fields"], dict["players"])

  def to_dict(self):
    return { "fields": self.get_field_names(), "players": self.players() }

  def to_packet_array(self):
    rv = [str(len(self._names))]
    rv.extend(self._names)
    rv.append(str(len(self._players)))
    for player in self._players:
      rv.extend(player)
    return rv

  @staticmethod
  def from_packet_array(a):
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

class Map(OpenStruct):
  pass
