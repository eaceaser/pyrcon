import logging

import gevent.pool

import frostbite.commands
from base import FBBase

from gevent import socket, queue
from gevent.event import AsyncResult

logger = logging.getLogger("FBClient")

class FBClient(FBBase):
  """Client to a Frostbite 2 compatible server."""
  def __init__(self, hostname, port, handler):
    FBBase.__init__(self, None, lambda x,y,z: x, handler)
    self.hostname = hostname
    self.port = port

  def start(self):
    """Starts the client's asynchronous processing units."""

    address = (socket.gethostbyname(self.hostname), self.port)
    logger.info("Connecting to %r" % (address,))
    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self._socket.connect(address)
    self._start_processors()
    return self

  def send(self, command):
    """
    Sends a message to the Frostbite server and returns a handle to receive the
    result at a later time.

    :param command: Frostbite Command structure to send to the server.
    :return: :mod:`gevent.queue.AsyncResult`
    """
    response = AsyncResult()
    packet = command.toPacket(self._next_seq())
    self._inflight[packet.seqNumber] = (command.response, response)
    self._send_queue.put(packet)
    return response
