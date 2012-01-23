from eventhandler import EventHandler

import gevent
import logging

logger = logging.getLogger("ProgressiveModes")
class ProgressiveModes(EventHandler):
  def __init__(self, control, config):
    self._control = control
    self._config = config
    self._get_server_info()

    # yes i know this is crappy
    self._current_mode = None
    self._modes = config["modes"]
    last_min = 0
    self._players_to_modes = []
    for mode in self._modes:
      limit = mode["limit"]
      self._players_to_modes.extend([mode for num in range(last_min, limit)])
      last_min = limit

    self._max_threshold = self._config["max_player_threshold"]
    self._num_rounds_before_switching = self._config["num_rounds_before_switching"]
    self._num_rounds_at_max = 0
    num_players = self._info["player_count"]
    current_mode = self._players_to_modes[num_players]

    gevent.spawn(self._set_current_mode, current_mode)

    logger.debug("Initialized ProgressiveModes.")

  def _set_current_mode(self, mode):
    mode_name = mode["mode"]
    num_rounds = mode["rounds_per_map"]
    logger.debug("Setting current mode to: %s" % mode_name)
    self._server().clearMapList().get()
    for map in mode["maps"]:
      self._server().addMap(map, mode_name, num_rounds).get()
    self._server().setNextMap(0)
    self._current_mode == mode_name

  def _server(self):
    return self._control.server

  def _get_server_info(self):
    self._info = self._control.server.info().get()

  def on_round_over_players(self, players):
    # record number of players.
    self._get_server_info()
    num_players = len(players)
    if num_players >= (self._info["max_players"] - self._max_threshold):
      logger.debug("Round ended with enough players.")
      self._num_rounds_at_max += 1
    else:
      logger.debug("Round ended without enough players. Resetting count.")
      self._num_rounds_at_max = 0
      if self._current_mode != self._players_to_modes[num_players]["mode"]:
        logger.debug("Should be running a different mode. Switching.")
        self._set_current_mode(self._players_to_modes[num_players])

    if self._num_rounds_at_max >= self._num_rounds_before_switching:
      logger.debug("Switching game modes!")
      self._set_current_mode(self._players_to_modes[self._info["max_players"] + 1])

module = ProgressiveModes