from frostbite.packet import Packet

class FrostbiteMessage:
  def toPacket(self, seq):
    return Packet(False, False, seq, self.words)

  filter = lambda p: p
#  def getResponse(self):
#    return self.response()

#class VersionResponse(FrostbiteResponse):
#  def getVersion(self):
#    print self.get().words[1:]

class Version(FrostbiteMessage):
  words = ["version"]
  filter = lambda g,p: " ".join(p.words[1:])
