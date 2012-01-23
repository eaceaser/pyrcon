import os
import binascii

import frostbite.commands
from frostbite.server import FBServer
from frostbite.serverstructs import ServerState, PlayerCollection

from gevent import event
from gevent.server import StreamServer

# BF3 Proxy server that listens with the frostbite protocol
class Proxy(object):
  def __init__(self, control):
    self._control = control
    self._handler = lambda socket, address: FBServer(socket, address, self._handle_command, self._handle_event).start().join()
    self._server = StreamServer(('0.0.0.0', 27260), self._handler)
    self._server.start()

  def _handle_command(self, server, seq, command):
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
    elif isinstance(command, frostbite.commands.Version):
      version = self._control.server.version().get()
      t = frostbite.commands.ResponsePacket("OK", *version.split(" "))
      server.send(seq, t)
    elif isinstance(command, frostbite.commands.ServerInfo):
      info = self._control.server.info().get()
      arr = ServerState.from_dict(info)
      server.send(seq, frostbite.commands.ResponsePacket("OK", *arr.to_packet_array()))
    elif isinstance(command, frostbite.commands.AdminListPlayers):
      players = self._control.server.listPlayers().get()
      pa = PlayerCollection.from_dict(players).to_packet_array()
      server.send(seq, frostbite.commands.ResponsePacket("OK", *pa))
    elif isinstance(command, frostbite.commands.FrostbiteVariable):
      var_name = command.words[0]
      rv = self._control.server.get_variable(var_name)
      server.send(seq, frostbite.commands.ResponsePacket("OK", rv.get()))
    else:
      server.send(seq, frostbite.commands.ResponsePacket("OK"))

  def _handle_event(self, event):
    pass
