import logging

from client import FBBase
from gevent.event import AsyncResult

logger = logging.getLogger("FBServer")
class FBServer(FBBase):
  def __init__(self, socket, address, command_handler, event_handler):
    FBBase.__init__(self, socket, command_handler, event_handler)

  def start(self):
    logger.info("Frostbite Server Started.")
    self.sent_salt = None
    self._start_processors()
    return self

  def send(self, seq, command):
    response = AsyncResult()
    packet = command.toPacket(seq)
    self._inflight[packet.seqNumber] = (command.filter, response)
    self._send_queue.put(packet)
    return response