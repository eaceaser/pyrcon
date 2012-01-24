import logging

import gevent
from gevent.event import AsyncResult
from gevent import socket, queue

from frostbite.packet import Packet
import frostbite.commands

logger = logging.getLogger("FBBase")
class FBBase(object):
  """Represents the base implementation of a frostbite communication class.

  Arguments:

  * ``socket``: GEvent socket.
  * ``command_handler``: Callback that gets passed a command when received off of the socket.
  * ``event_handler``: Callback that gets passed an event when received off of the socket.
  """
  def __init__(self, socket, command_handler, event_handler):
    self.seq = 0
    self._command_handler = command_handler
    self._event_handler = event_handler
    self._socket = socket
    self._send_queue = gevent.queue.Queue()
    self._read_queue = gevent.queue.Queue()
    self._inflight = {}
    self._group = gevent.pool.Group()

  def _start_processors(self):
    self._group.spawn(self._send_loop)
    self._group.spawn(self._read_loop)
    self._group.spawn(self._process_loop)

  def _next_seq(self):
    seq = self.seq
    self.seq += 1
    return seq

  def _write(self, packet):
    self._send_queue.put(packet)

  def _send_loop(self):
    while True:
      packet = self._send_queue.get()
      logger.debug("Writing packet inflight: %s %s" % (packet.seqNumber, packet.words))
      try:
        self._socket.sendall(packet.encode())
      except Exception:
        logger.info("Connection closed.")
        self.stop()
#        self._group.kill()
        return

  def _read_loop(self):
    buf = ''
    while True:
      try:
        data = self._socket.recv(512)
      except Exception:
        logger.info("Connection closed.")
#        self._group.kill()
        return

      if data is None:
        logger.info("Empty data, no more connection.")
#        self._group.kill()
        return

      buf += data
      while len(buf) > Packet.processSize:
        packet, buf = Packet.decode(buf)
        logger.debug("Received data and decoded a packet.")
        self._read_queue.put(packet)

  def _process_loop(self):
    while True:
      packet = self._read_queue.get()
      if packet.isResponse:
        self._handle_response(packet)
      else:
        self._handle_command(packet)

  def _handle_response(self, packet):
    filt, response = self._inflight[packet.seqNumber]
    if response is not None:
      del(self._inflight[packet.seqNumber])
      gevent.spawn(filt, packet, self).link(response)
      logger.debug("Received response for %s: %s" % (packet.seqNumber, packet))
    else:
      logger.err("Message received for an unknown sequence: %s", (packet.seqNumber))

  def _handle_command(self, packet):
    """Handle a packet that is a command directive.

    Arguments:
    - packet: A Frostbite message packet.
    """
    method = packet.words[0]

    generator = frostbite.commands.message_generators.get(method, None)
    if generator is not None:
      logger.debug("Message received: %s" % packet)
      message = generator(packet)
      if isinstance(message, frostbite.commands.FrostbiteEvent):
        logger.debug("Message is an event. Handing off to event handler.")
        gevent.spawn(self._event_handler, self, packet.seqNumber, message)
      elif isinstance(message, frostbite.commands.FrostbiteVariable):
        logger.debug("Message is a variable. Handing off to command handler.")
        gevent.spawn(self._command_handler, self, packet.seqNumber, message)
      else:
        logger.debug("Message is a command. Handing off to command handler.")
        gevent.spawn(self._command_handler, self, packet.seqNumber, message)
    else:
      logger.debug("Unknown message: %s" % packet)

  def stop(self):
    """Stops the protocol's async processing units."""
    self._group.kill()
    if self._socket is not None:
      self._socket.close()
      self._socket = None

  def join(self):
    """Joins to the protocol's async processing units."""
    self._group.join()