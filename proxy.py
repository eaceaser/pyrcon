import os
import binascii

import frostbite.commands
from frostbite.server import FBServer
from frostbite.serverstructs import ServerState

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
    if isinstance(command, frostbite.commands.LoginRequest):
      salt = self._control.getSalt()
      salt_response = frostbite.commands.ResponsePacket("OK", salt)
      server.sent_salt = salt
      server.send(seq, salt_response)
    elif isinstance(command, frostbite.commands.LoginSecret):
      if self._control.auth(server.sent_salt, command.secret):
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
    elif isinstance(command, frostbite.commands.AdminListAllPlayers):
      players = self._control.server.listPlayers().get()
      pa = players.to_packet_array()
      server.send(seq, frostbite.commands.ResponsePacket("OK", *pa))
    else:
      server.send(seq, frostbite.commands.ResponsePacket("OK"))

  def _handle_event(self, event):
    pass
