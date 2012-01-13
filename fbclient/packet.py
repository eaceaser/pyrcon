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
    word_cnt = len(self.words)
    packet_size = 12 + reduce(lambda x,y: x+5+len(y), self.words, 0)
    packet = struct.pack("<III", header, packet_size, word_cnt)
    for word in self.words:
      enc = ""
      enc += struct.pack("<I", len(word))
      enc += word.encode("cp1252")
      enc += chr(0)
      packet += enc

    return packet

  def strtoword(string):
    return string

  def decode(buf):
    pass
