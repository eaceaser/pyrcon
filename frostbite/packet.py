import struct

HEADER_LENGTH = 12

class Packet(object):
  """Represents a deserialized Frostbite RCon protocol Packet."""

  processSize = HEADER_LENGTH
  """The minimum size of a byte array before it is eligible to be parsed into a Packet."""

  def __init__(self, originatedFromServer, isResponse, seqNumber, words):
    """Initializes a Packet.

    * originatedFromServer: Boolean, Indicates the message originated at the server.
    * isResponse: Boolean, Indicates that the message is in response to another.
    * seqNumber: ``Int``, Sequence number for message multiplexing.
    * words: ``strarray`` List of words that make up the message.
    """
    self.originatedFromServer = originatedFromServer
    self.isResponse = isResponse
    self.seqNumber = seqNumber
    self.words = [str(word) for word in words]

  def __str__(self):
    return "<Packet: originatedFromServer=%s isResponse=%s seqNumber=%i words=%s>" % (self.originatedFromServer, self.isResponse, self.seqNumber, self.words)

  def encode(self):
    """Encodes a packet into a byte string suitable for sending to a Frostbite server."""
    header = self.seqNumber & 0x3fffffff
    if self.originatedFromServer: header += 0x80000000
    if self.isResponse: header += 0x40000000
    word_cnt = len(self.words)
    packet_size = HEADER_LENGTH + reduce(lambda x,y: x+5+len(y), self.words, 0)
    packet = struct.pack("<III", header, packet_size, word_cnt)
    for word in self.words:
      enc = ""
      enc += struct.pack("<I", len(word))
      enc += word.encode("cp1252")
      enc += chr(0)
      packet += enc

    return packet

  @staticmethod
  def decode(buf):
    """Alternative constructor for a Packet structure.

    Takes a byte string of an encoded Frostbite server message, and returns a tuple of (packet, unused)
    where packet is the decoded packet, and unused is the unused bytes from the original buffer.
    """

    if len(buf) < HEADER_LENGTH:
      return (None, buf)
    packet_data = buf[:HEADER_LENGTH]
    (header, size, num_words) = struct.unpack("<III", packet_data)
    originated_from_server = (header & 0x80000000) != 0
    is_response = (header & 0x40000000) != 0
    seq_num = header & 0x3fffffff

    if len(buf) < size:
      return (None, buf)

    data,rest = buf[HEADER_LENGTH:size],buf[size:]
    pos = 0
    words = []
    for i in range(num_words):
      word_length, = struct.unpack("<I", data[pos:pos+4])
      words.append(data[pos+4:pos+4+word_length].decode("cp1252"))
      pos = pos + word_length + 4 + 1

    return (Packet(originated_from_server, is_response, seq_num, words), rest)
