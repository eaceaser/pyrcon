import os
import binascii

import frostbite.commands
from frostbite.server import FBServer
from frostbite.serverstructs import ServerState, PlayerCollection, MapList

from gevent import event
from gevent.server import StreamServer
from eventhandler import EventHandler

# BF3 Proxy server that listens with the frostbite protocol
class Proxy(object):
  def __init__(self, control):
    self._control = control
    self._handler = lambda socket, address: FBServer(socket, address, self._handle_command, self._handle_event).start().join()
    self._server = StreamServer(('0.0.0.0', 27260), self._handler)
    self._server.start()
    self._command_to_method = {}
    self._define_methods()

  def _define_proxy_method(self, command, method, extract_args=None, filter=None):
    def proxy(s, msg):
      args = []
      if extract_args is not None:
        args.extend(extract_args(msg))
      rv = method(*args).get()
      if filter is not None:
        rv = filter(rv)
      else:
        rv = []
      return frostbite.commands.ResponsePacket("OK", *rv)

    self._command_to_method[command] = proxy

  def _define_methods(self):
    d = self._define_proxy_method
    r = self._control.server

    d(frostbite.commands.Version, r.version, filter=lambda r: r.split(" "))
    d(frostbite.commands.ServerInfo, r.info, filter=lambda i: ServerState.from_dict(i).to_packet_array())
    d(frostbite.commands.AdminListPlayers, r.list_players, filter=lambda p: PlayerCollection.from_dict(p).to_packet_array())
    d(frostbite.commands.FrostbiteVariable, r.get_variable, filter=lambda v: [v], extract_args=lambda m:[m.words[0]])
    d(frostbite.commands.MapListList, r.list_maps, filter=lambda m: MapList.from_dict(m).to_packet_array())
    d(frostbite.commands.MapListGetMapIndices, r.get_map_indices)
    d(frostbite.commands.MapListRestartRound, r.restart_round)
    d(frostbite.commands.MapListRunNextRound, r.next_round)
    d(frostbite.commands.MapListEndRound, r.end_round, extract_args=lambda m:[m.winning_team])
    d(frostbite.commands.AdminSay, r.say, extract_args=lambda m:[m.message])

    for var in frostbite.commands.variable_types:
      type = frostbite.commands.variable_types[var]
      self._command_to_method[type] = self._command_to_method[frostbite.commands.FrostbiteVariable]

  def _handle_command(self, server, seq, command):
    method = self._command_to_method.get(type(command), None)
    if method is None:
      if isinstance(command, frostbite.commands.LoginHashed):
        if command.password is None:
          salt = self._control.get_salt()
          salt_response = frostbite.commands.ResponsePacket("OK", salt)
          server.sent_salt = salt
          server.send(seq, salt_response)
        else:
          if self._control.auth(server.sent_salt, command.password):
            server.send(seq, frostbite.commands.ResponsePacket("OK"))
          else:
            server.send(seq, frostbite.commands.ResponsePacket("InvalidPasswordHash"))
      if isinstance(command, frostbite.commands.AdminEventsEnabled):
        if server.events_enabled is False:
          self._control.server.add_event_handler(ProxyEventHandler(server))
          server.send(seq, frostbite.commands.ResponsePacket("OK"))
      else:
        print "Unknown method to proxy."
        server.send(seq, frostbite.commands.ResponsePacket("OK"))
    else:
      resp = method(self, command)
      server.send(seq, resp)

  def _handle_event(self, server, seq, event):
    # proxy the event.
    print "HI"
#    server.send(seq, event)

class ProxyEventHandler(EventHandler):
  def __init__(self, server):
    self.server = server
    self.server.events_enabled = True
    self._seq = 0

  def on_player_chat(self, name, text):
    self.server.send(self._seq, frostbite.commands.PlayerOnChat(name=name, text=text))
    self._seq += 1
