import time

from serverstate import ServerState

from packet import Packet
from twisted.internet.protocol import Protocol, Factory
from twisted.python import log

import hashlib

def hash_pass(salt, password):
  m = hashlib.md5()
  decoded = salt.decode('hex')
  m.update(decoded+password.encode("ascii"))
  return m.hexdigest()

class FBClientBase(Protocol):
  def __init__(self, callbacks):
    self.callbacks = callbacks

  def next_seq(self):
    seq = self.seq
    self.seq = self.seq + 1
    return seq

  def writePacket(self, packet):
    self.inflight[packet.seqNumber] = (packet.words[0], time.clock())
    log.msg("wrote inflight: %s %s" % (packet.seqNumber, packet.words))
    self.transport.write(packet.encode())

  def readPacket(self):
    packet, self.buf = Packet.decode(self.buf)
    return packet

  def connectionMade(self):
    self.seq = 0
    self.buf = ''
    self.inflight = {}

  def connectionLost(self, reason):
    print "lost connection: %s" % reason

  def dataReceived(self, data):
    self.buf = self.buf + data
    while len(self.buf) > 0:
      packet = self.readPacket()
      method, time = self.inflight[packet.seqNumber]
      del(self.inflight[packet.seqNumber])
      log.msg("Received response for %s: %s" % (packet.seqNumber, method))
      callback = getattr(self.callbacks, method.replace(".", "_"), None)
      if callback == None:
        log.err("Unknown method: %s" % method)
        log.err("Words received: %s" % packet.words)
      else:
        callback(self, packet)

class FBClient(FBClientBase):
  def __init__(self, callbacks):
    self.callbacks = callbacks

  def serverInfo(self):
    server_info = Packet(False, False, self.next_seq(), ["serverInfo"])
    self.writePacket(server_info)

  def version(self):
    version = Packet(False, False, self.next_seq(), ["version"])
    self.writePacket(version)

  def login(self):
    login = Packet(False, False, self.next_seq(), ["login.hashed"])
    self.writePacket(login)

  def loginWithPass(self, password):
    login = Packet(False, False, self.next_seq(), ["login.hashed", password])
    self.writePacket(login)

class FBClientCallbacks:
  def __init__(self, config):
    self.serverstate = ServerState()
    self.config = config

  def serverInfo(self, protocol, packet):
    self.serverstate.serverName = packet.words[1]
    self.serverstate.playerCount = int(packet.words[2])
    self.serverstate.maxPlayers = int(packet.words[3])
    self.serverstate.gameMode = packet.words[4]
    self.serverstate.mapName = packet.words[5]
    self.serverstate.currentRound = int(packet.words[6])
    self.serverstate.totalRounds = packet.words[7]
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
    self.serverstate.joinAddress = packet.words[8+numTeams+8]
    self.serverstate.punkbusterVersion = packet.words[8+numTeams+9]
    self.serverstate.joinQueueEnabled = packet.words[8+numTeams+10]
    self.serverstate.region = packet.words[8+numTeams+11]
    self.serverstate.pingSite = packet.words[8+numTeams+12]
    self.serverstate.country = packet.words[8+numTeams+13]

  def version(self, protocol, packet):
    version = " ".join(packet.words[1:])
    self.serverstate.version = version

  def login_hashed(self, protocol, packet):
    rv = packet.words[0]
    if rv == u'InvalidPasswordHash':
      log.err("Invalid password hash")
      return

    if len(packet.words) > 1:
      salt = packet.words[1]
      hashed = hash_pass(salt, self.config.password)
      protocol.loginWithPass(hashed.upper())
    else:
      log.msg("Logged in successfully.")

class FBFactory(Factory):
  def __init__(self, config):
    self.config = config

  def buildProtocol(self, addr):
    return FBClient(FBClientCallbacks(self.config))
