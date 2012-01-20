import os
import binascii

import frostbite.commands
from frostbite.server import FBServer
from frostbite.serverstructs import ServerState

from gevent import event
from gevent.server import StreamServer

# BF3 Proxy server that listens with the frostbite protocol
class Proxy(object):
  def __init__(self, client):
    self._client = client
    self._handler = lambda socket, address: FBServer(socket, address, self._handle_command, self._handle_event).start()
    self._server = StreamServer(('0.0.0.0', 27260), self._handler)
    self._server.start()

  def _handle_command(self, server, seq, command):
    if isinstance(command, frostbite.commands.LoginRequest):
      salt = frostbite.commands.ResponsePacket("OK", self._generate_salt().upper())
      server.send(seq, salt)
    elif isinstance(command, frostbite.commands.LoginSecret):
      t = frostbite.commands.ResponsePacket("OK")
      server.send(seq, t)
    elif isinstance(command, frostbite.commands.Version):
      version = self._client.version().get()
      t = frostbite.commands.ResponsePacket("OK", *version.split(" "))
      server.send(seq, t)
    elif isinstance(command, frostbite.commands.ServerInfo):
      info = self._client.info().get()
      arr = ServerState.from_dict(info)
      server.send(seq, frostbite.commands.ResponsePacket("OK", *arr.to_packet_array()))
    elif isinstance(command, frostbite.commands.AdminListAllPlayers):
      players = self._client.listPlayers().get()
      pa = players.to_packet_array()
      server.send(seq, frostbite.commands.ResponsePacket("OK", *pa))
    else:
      server.send(seq, frostbite.commands.ResponsePacket("OK"))

  def _handle_event(self, event):
    pass

  def _generate_salt(self):
    salt = os.urandom(32)
    return binascii.hexlify(salt)

