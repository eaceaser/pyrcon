import time
import logging

import gevent.pool
from gevent.event import AsyncResult
from gevent import socket, queue

import frostbite.commands
from frostbite.packet import Packet

logger = logging.getLogger("FBClient")
class FBClient(object):
  seq = 0

  def __init__(self, hostname, port, handler):
    self.hostname = hostname
    self.port = port
    self._handler = handler
    self._socket = None
    self._send_queue = gevent.queue.Queue()
    self._read_queue = gevent.queue.Queue()
    self._inflight = {}
    self._group = gevent.pool.Group()

  def start(self):
    address = (socket.gethostbyname(self.hostname), self.port)
    logger.info("Connecting to %r" % (address,))
    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self._socket.connect(address)
    self._group.spawn(self._send_loop)
    self._group.spawn(self._read_loop)
    self._group.spawn(self._process_loop)

  def _next_seq(self):
    seq = self.seq
    self.seq = self.seq + 1
    return seq

  def _write(self, packet):
    self._send_queue.put(packet)

  def _send_loop(self):
    while True:
      packet = self._send_queue.get()
      logger.debug("Writing packet inflight: %s %s" % (packet.seqNumber, packet.words))
      self._socket.sendall(packet.encode())

  def _read_loop(self):
    buf = ''
    while True:
      data = self._socket.recv(512)
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
        self._handle_event(packet)

  def _handle_response(self, packet):
    filt, response = self._inflight[packet.seqNumber]
    if response is not None:
      del(self._inflight[packet.seqNumber])
      gevent.spawn(filt, packet, self).link(response)
      logger.debug("Received response for %s: %s" % (packet.seqNumber, packet))
    else:
      logger.err("Message received for an unknown sequence: %s", (packet.seqNumber))

  def _handle_event(self, packet):
    event = packet.words[0]
    logger.debug("Event received: %s" % packet)
    try:
      builder = frostbite.commands.events[event]
      command = builder(packet)
      gevent.spawn(self._handler, command)
    except KeyError:
      logger.debug("No handler found for event.")

  def stop(self):
    self._group.kill()
    if self._socket is not None:
      self._socket.close()
      self._socket = None

  def join(self):
    self._group.join()

  def send(self, command):
    response = AsyncResult()
    packet = command.toPacket(self._next_seq())
    self._inflight[packet.seqNumber] = (command.filter, response)
    self._send_queue.put(packet)
    return response
