from frostbite import crypt, client, commands

import gevent
from gevent import event

# class which contains stateful knowledge of a BF3 Server
class BFServer(object):
  def __init__(self, host, port, password):
    self._host = host
    self._port = port
    self._password = password
    self._client = None
    self._loggedIn = False
    self._mapListLoaded = False
    self._events = {}
    self._handlers = []

    self._define_events()
    self._define_methods()

    self._attemptConnect()
    self._login()
    self._enable_events()

  def _login(self):
    assert self._has_client()
    salt_command = commands.LoginHashed()
    salt_response = self._client.send(salt_command)
    salt = salt_response.get()

    login_command = commands.LoginHashed(password=crypt.hash_pass(salt, self._password))
    loginResponse = self._client.send(login_command)
    response = loginResponse.get()
    self._loggedIn = True
    self._event_handlers = []

  def _has_client(self):
    return self._client is not None

  def _is_logged_in(self):
    return self._has_client() and self._loggedIn is True

  def _attemptConnect(self):
    self._client = client.FBClient(self._host, self._port, self._dispatch_event)
    self._client.start()

  def _define_method_wrapper(self, method_name, message_type, arg_names=[], defaults={}, out=None, assertion=None):
    def method(*args):
      if assertion is not None:
        assertion()

      kwargs = {}
      for key in defaults:
        kwargs[key] = defaults[key]
      if arg_names is not None:
        for name, arg in map(None, arg_names, args):
          kwargs[name] = arg

      msg = message_type(**kwargs)
      msg_rv = self._client.send(msg)
      if out is not None:
        rv = event.AsyncResult()
        gevent.spawn(out, msg_rv).link(rv)
        return rv
      else:
        return msg_rv
    setattr(self, method_name, method)
    self.__dict__[method_name] = method

  def _define_methods(self):
    d = self._define_method_wrapper
    d("version", commands.Version, assertion=self._has_client)
    d("next_round", commands.MapListRunNextRound, assertion=self._is_logged_in)
    d("restart_round", commands.MapListRestartRound, assertion=self._is_logged_in)
    d("end_round", commands.MapListEndRound, ["winning_team"], assertion=self._is_logged_in)
    d("info", commands.ServerInfo, out=lambda r:r.get().to_dict(), assertion=self._has_client)
    d("list_maps", commands.MapListList, out=lambda r:r.get().to_dict(), assertion=self._is_logged_in)
    d("get_map_indices", commands.MapListGetMapIndices, assertion=self._is_logged_in)
    d("add_map", commands.MapListAdd, ["map_name", "gamemode", "rounds"], defaults={"index": 0}, assertion=self._is_logged_in)
    d("set_next_map", commands.MapListSetNextMapIndex, ["index"], assertion=self._is_logged_in)
    d("clear_map_list", commands.MapListClear, assertion=self._is_logged_in)
    d("save_map_list", commands.MapListSave, assertion=self._is_logged_in)
    d("remove_map", commands.MapListRemove, ["index"], assertion=self._is_logged_in)
    d("list_all_players", commands.AdminListPlayers, out=lambda r:r.get().to_dict(), defaults={"scope":"all"}, assertion=self._is_logged_in)
    d("kick_player", commands.AdminKickPlayer, ["player_name", "reason"], assertion=self._is_logged_in)
    d("kill_player", commands.AdminKillPlayer, ["player_name"], assertion=self._is_logged_in)
    d("add_ban", commands.BanListAdd, ["id_type", "id", "timeout", "reason"], assertion=self._is_logged_in)
    d("list_bans", commands.BanListList, assertion=self._is_logged_in, out=lambda bl:[b.to_dict() for b in bl.get()])
    d("say_all", commands.AdminSay, ["message"], defaults={"scope":"all"}, assertion=self._is_logged_in)

  def _define_event_dispatch(self, message, dispatch):
    self._events[message] = dispatch

  def _define_events(self):
    d = self._define_event_dispatch
    d(commands.PlayerOnAuthenticated,
      lambda h,c: h.on_player_authenticated(c.name))
    d(commands.PlayerOnJoin,
      lambda h,c: h.on_player_join(c.name, c.guid))
    d(commands.PlayerOnLeave,
      lambda h,c: h.on_player_leave(c.name, c.info))
    d(commands.PlayerOnSpawn,
      lambda h,c: h.on_player_spawn(c.name, c.team))
    d(commands.PlayerOnKill,
      lambda h,c: h.on_player_kill(c.killer, c.killed, c.weapon, c.headshot))
    d(commands.PlayerOnChat,
      lambda h,c: h.on_player_chat(c.name, c.text))
    d(commands.PlayerOnSquadChange,
      lambda h,c: h.on_player_squad_change(c.name, c.team, c.squad))
    d(commands.PlayerOnTeamChange,
      lambda h,c: h.on_player_team_change(c.name, c.team, c.squad))
    d(commands.PunkBusterOnMessage,
      lambda h,c: h.on_punkbuster_message(c.message))
    d(commands.ServerOnLevelLoaded,
      lambda h,c: h.on_level_loaded(c.name, c.gamemode, c.rounds_played, c.rounds_total))
    d(commands.ServerOnRoundOver,
      lambda h,c: h.on_round_over(c.winning_team))
    d(commands.ServerOnRoundOverPlayers,
      lambda h,c: h.on_round_over_players(c.players))
    d(commands.ServerOnRoundOverTeamScores,
      lambda h,c: h.on_round_over_team_scores(c.team_scores))

  def _dispatch_event(self, client, seq, command):
    dispatch = self._events.get(type(command), None)
    if dispatch is not None:
      for handler in self._handlers:
        gevent.spawn(dispatch, handler, command)
    else:
      log.debug("Unknown event: %s" % command)

  def _enable_events(self):
    assert self._is_logged_in()
    msg = commands.AdminEventsEnabled(enable=True)
    rv = self._client.send(msg)
    rv.get()

  def add_event_handler(self, handler):
    self._handlers.append(handler)

  def list_variables(self):
    #TODO: Define variables here to decouple from frostbite.
    assert self._is_logged_in()
    outer_rv = event.AsyncResult()
    rvs = []
    for var_type in commands.variable_types.values():
      var = var_type(None)
      var_rv = event.AsyncResult()
      rv = self._client.send(var)
      gevent.spawn(lambda v,r: [v.words[0], r.get()], var, rv).link(var_rv)
      rvs.append(var_rv)

    gevent.spawn(lambda rs: dict([p.get() for p in rs]), rvs).link(outer_rv)
    return outer_rv

  def set_variable(self, key, val):
    assert self._is_logged_in()
    variable = commands.variable_types[key](value=val)
    rv = self._client.send(variable)
    return rv

  def get_variable(self, key):
    assert self._is_logged_in()
    variable = commands.variable_types[key]()
    rv = self._client.send(variable)
    return rv

  def say(self, message):
    return self.say_all(message)
