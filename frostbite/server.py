import logging

from client import FBBase
from gevent.event import AsyncResult

logger = logging.getLogger("FBServer")
class FBServer(FBBase):
  """Server that listens on a configured port and handles Frostbite 2 compatible commands.

    :param socket:
    :param address:
    :param command_handler:
    :param event_handler:
    :return:
  """
  def __init__(self, socket, address, command_handler, event_handler):
    FBBase.__init__(self, socket, command_handler, event_handler)
    self.events_enabled = False

  def start(self):
    """
    Starts the Frostbite server's event processor.

    Called by the :mod:`gevent.TCPServer` listener.
    :return: Returns itself to allow chaining.
    """
    logger.info("Frostbite Server Started.")
    self.sent_salt = None
    self._start_processors()
    return self

  def send(self, seq, command):
    """
    Sends a message to the client attached to this server. Returns a handle
    to retrieve the response at a later time.

    :param seq: Sequence number of this message.
    :param command: Frostbite Command structure.
    :return: :mod:`gevent.queue.AsyncResult`
    """
    response = AsyncResult()
    packet = command.toPacket(seq)
    self._inflight[packet.seqNumber] = (command.response, response)
    self._send_queue.put(packet)
    return response