import frostbite.commands

from frostbite.server import FBServer
from frostbite.serverstructs import ServerState, MapList, Map, PlayerCollection, Ban
from gevent.server import StreamServer

class TestServer(object):
  def __init__(self):
    self._handler = lambda socket, address: FBServer(socket, address, self._handle_command, self._handle_event).start().join()
    self._server = StreamServer(('0.0.0.0', 28260), self._handler)
    self._server.start()
    self.last_command = None

  def _handle_command(self, server, seq, command):
    if isinstance(command, frostbite.commands.LoginHashed):
      if command.password is None:
        server.send(seq, frostbite.commands.ResponsePacket("OK", "1234"))
      else:
        server.send(seq, frostbite.commands.ResponsePacket("OK"))
    elif isinstance(command, frostbite.commands.Version):
      server.send(seq, frostbite.commands.ResponsePacket("OK", "TestServer 1"))
    elif isinstance(command, frostbite.commands.ServerInfo):
      state = ServerState("testServer", 1, 16, "testmode0", "MP_Test", 1, 2, 2, [200, 200], 200, "", True, True, False, "1234", "200", "", "1.0", False, "US", "SF", "US")
      server.send(seq, frostbite.commands.ResponsePacket("OK", *state.to_packet_array()))
    elif isinstance(command, frostbite.commands.MapListRunNextRound):
      self.last_command = "next_round"
      server.send(seq, frostbite.commands.ResponsePacket("OK"))
    elif isinstance(command, frostbite.commands.MapListRestartRound):
      self.last_command = "restart_round"
      server.send(seq, frostbite.commands.ResponsePacket("OK"))
    elif isinstance(command, frostbite.commands.MapListEndRound):
      self.last_command = "end_round %s" % command.winning_team
      server.send(seq, frostbite.commands.ResponsePacket("OK"))
    elif isinstance(command, frostbite.commands.MapListList):
      maps = MapList([Map("MP_Test1", "TestMode0", 2), Map("MP_Test2", "TestMode1", 5)])
      server.send(seq, frostbite.commands.ResponsePacket("OK", *maps.to_packet_array()))
    elif isinstance(command, frostbite.commands.MapListGetMapIndices):
      server.send(seq, frostbite.commands.ResponsePacket("OK", "0", "1"))
    elif isinstance(command, frostbite.commands.MapListAdd):
      self.last_command = "add_map %s %s %s" % (command.map_name, command.gamemode, command.rounds)
      server.send(seq, frostbite.commands.ResponsePacket("OK"))
    elif isinstance(command, frostbite.commands.MapListSetNextMapIndex):
      self.last_command = "set_next_map %s" % command.index
      server.send(seq, frostbite.commands.ResponsePacket("OK"))
    elif isinstance(command, frostbite.commands.MapListClear):
      self.last_command = "clear_map_list"
      server.send(seq, frostbite.commands.ResponsePacket("OK"))
    elif isinstance(command, frostbite.commands.MapListSave):
      self.last_command = "save_map_list"
      server.send(seq, frostbite.commands.ResponsePacket("OK"))
    elif isinstance(command, frostbite.commands.MapListRemove):
      self.last_command = "remove_map %s" % command.index
      server.send(seq, frostbite.commands.ResponsePacket("OK"))
    elif isinstance(command, frostbite.commands.AdminListPlayers):
      list = PlayerCollection(["field1", "field2", "field3"], [["what", "the", "crap"]])
      server.send(seq, frostbite.commands.ResponsePacket("OK", *list.to_packet_array()))
    elif isinstance(command, frostbite.commands.AdminKickPlayer):
      self.last_command = "kick_player %s %s" % (command.player_name, command.reason)
      server.send(seq, frostbite.commands.ResponsePacket("OK"))
    elif isinstance(command, frostbite.commands.AdminKillPlayer):
      self.last_command = "kill_player %s" % (command.player_name)
      server.send(seq, frostbite.commands.ResponsePacket("OK"))
    elif isinstance(command, frostbite.commands.BanListAdd):
      self.last_command = "add_ban %s %s %s %s" % (command.id_type, command.id, command.timeout, command.reason)
      server.send(seq, frostbite.commands.ResponsePacket("OK"))
    elif isinstance(command, frostbite.commands.BanListList):
      list = [Ban("guid", "random-id", "forever", "100", "no reason")]
      flat = []
      for b in list:
        flat.extend(b.to_packet_array())

      server.send(seq, frostbite.commands.ResponsePacket("OK", len(list), *flat))
    elif isinstance(command, frostbite.commands.AdminSay):
      self.last_command = "say %s %s" % (command.scope, command.message)
      server.send(seq, frostbite.commands.ResponsePacket("OK"))
    else:
      server.send(seq, frostbite.commands.ResponsePacket("OK"))

  def _handle_event(self):
    pass
