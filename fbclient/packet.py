import struct

class Packet:
  def __init__(self, originatedFromServer, isResponse, seqNumber, words):
    self.originatedFromServer = originatedFromServer
    self.isResponse = isResponse
    self.seqNumber = seqNumber
    self.words = words

  def encode(self):
    header = self.seqNumber & 0x3fffffff
    if self.originatedFromServer: header += 0x80000000
    if self.isResponse: header += 0x40000000
    packet_size = 12
    words = 0
    packet = struct.pack(">III", header, packet_size, words)
    return packet
