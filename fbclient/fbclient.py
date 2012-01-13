import struct

from packet import Packet
from twisted.internet.protocol import Protocol

class FBClient(Protocol):
  def next_seq(self):
    seq = self.seq
    self.seq = self.seq + 1
    return seq

  def readPacket(self):
    print "HI"
    if len(self.buf) < header_length: return
    packet_data = self.buf[:header_length]
    packet = Packet(packet_data)
    (header, size, words) = struct.unpack(">III", self.buf[:length])
    originated_from_server = (header & 0x80000000) != 0
    is_response = header & 0x40000000
    seq_num = header & 0x3fffffff

    data,self.buf = self.buf[header_length:size],self.buf[size:]
    pos = 0
    words = []
    for i in range(words):
      word_length = Struct.unpack(">I", data[pos])
      words.append(data[pos+4:word_length].decode("cp1252"))
      pos = pos + word_length + 4 + 1

  def connectionMade(self):
    print "connected!"
    self.seq = 0
    self.buf = ''
    packet = Packet(False, False, self.next_seq(), ["version"])
    self.transport.write(packet.encode())

  def connectionLost(self, reason):
    print "lost connection: %s" % reason

  def dataReceived(self, data):
    print "received data: %s" % data
    self.buf = self.buf + data
