import time

from serverstate import ServerState

from packet import Packet
from twisted.internet.protocol import Protocol, Factory
from twisted.python import log

class FBClient(Protocol):
  def __init__(self, callbacks):
    self.callbacks = callbacks

  def next_seq(self):
    seq = self.seq
    self.seq = self.seq + 1
    return seq

  def writePacket(self, packet):
    self.inflight[packet.seqNumber] = (packet.words, time.clock())
    log.msg("wrote inflight: %s %s" % (packet.seqNumber, packet.words))
    self.transport.write(packet.encode())

  def readPacket(self):
    packet, self.buf = Packet.decode(self.buf)
    return packet

  def connectionMade(self):
    self.seq = 0
    self.buf = ''
    self.inflight = {}
    server_info = Packet(False, False, self.next_seq(), ["serverInfo"])
    self.writePacket(server_info)
    version = Packet(False, False, self.next_seq(), ["version"])
    self.writePacket(version)

  def connectionLost(self, reason):
    print "lost connection: %s" % reason

  def dataReceived(self, data):
    self.buf = self.buf + data
    while len(self.buf) > 0:
      packet = self.readPacket()
      methods, time = self.inflight[packet.seqNumber]
      log.msg("Received response for %s: %s" % (packet.seqNumber, methods))
      for method in methods:
        callback = getattr(self.callbacks, method, None)
        if callback == None:
          log.err("Unknown method: %s" % method)
        else:
          callback(packet)

class Callbacks:
  def __init__(self, serverstate):
    self.serverstate = serverstate

  def serverInfo(self, packet):
    self.serverstate.serverName = packet.words[1]
    self.serverstate.playerCount = int(packet.words[2])
    self.serverstate.maxPlayers = int(packet.words[3])
    self.serverstate.gameMode = packet.words[4]
    self.serverstate.mapName = packet.words[5]
    self.serverstate.currentRound = int(packet.words[6])
    self.serverstate.totalRounds = int(packet.words[7])
    self.serverstate.numTeams = int(packet.words[8])
    numTeams = self.serverstate.numTeams
    self.serverstate.teamScores = []
    for i in range(self.serverstate.numTeams):
      self.serverstate.teamScores.append(int(packet.words[8+i+1]))
    self.serverstate.targetScores = int(packet.words[8+numTeams+1])
    self.serverstate.onlineState = packet.words[8+numTeams+2]
    self.serverstate.isRanked = packet.words[8+numTeams+3]
    self.serverstate.hasPunkbuster = packet.words[8+numTeams+4]
    self.serverstate.hasPassword  = packet.words[8+numTeams+5]
    self.serverstate.serverUptime = int(packet.words[8+numTeams+6])
    self.serverstate.roundTime = int(packet.words[8+numTeams+7])
    self.serverstate.gameMod = packet.words[8+numTeams+8]
    self.serverstate.mapPack = packet.words[8+numTeams+9]
    self.serverstate.joinAddress = packet.words[8+numTeams+10]
    self.serverstate.punkbusterVersion = packet.words[8+numTeams+11]
    self.serverstate.joinQueueEnabled = packet.words[8+numTeams+12]
    self.serverstate.dunno = packet.words[8+numTeams+13]
    self.serverstate.serverRegion = packet.words[8+numTeams+13]
    log.msg(self.serverstate)

class FBFactory(Factory):
  def buildProtocol(self, addr):
    return FBClient(Callbacks(ServerState()))
