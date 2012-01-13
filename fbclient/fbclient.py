from packet import Packet
from twisted.internet.protocol import Protocol

class FBClient(Protocol):
  def next_seq(self):
    seq = self.seq
    self.seq = self.seq + 1
    return seq

  def readPacket(self):
    packet, self.buf = Packet.decode(self.buf)
    print packet

  def connectionMade(self):
    self.seq = 0
    self.buf = ''
    server_info = Packet(False, False, self.next_seq(), ["serverInfo"])
    self.transport.write(server_info.encode())
    version = Packet(False, False, self.next_seq(), ["version"])
    self.transport.write(version.encode())

  def connectionLost(self, reason):
    print "lost connection: %s" % reason

  def dataReceived(self, data):
    self.buf = self.buf + data
    while len(self.buf) > 0:
      self.readPacket()
