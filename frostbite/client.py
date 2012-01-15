import time

from serverstate import ServerState

from packet import Packet
from twisted.internet import protocol, defer
from twisted.python import log

import hashlib

def hash_pass(salt, password):
  m = hashlib.md5()
  decoded = salt.decode('hex')
  m.update(decoded+password.encode("ascii"))
  return m.hexdigest()

class FBClientBase(protocol.Protocol):
  buffer = ""
  seq = 0

  def next_seq(self):
    seq = self.seq
    self.seq = self.seq + 1
    return seq

  def writePacket(self, packet, deferred):
    self.inflight[packet.seqNumber] = (packet.words[0], deferred, time.clock())
    log.msg("wrote inflight: %s %s" % (packet.seqNumber, packet.words))
    self.transport.write(packet.encode())

  def readPacket(self):
    packet, self.buffer = Packet.decode(self.buffer)
    return packet

  def connectionMade(self):
    self.seq = 0
    self.buffer = ""
    self.inflight = {}

  def connectionLost(self, reason):
    print "lost connection: %s" % reason

  def dataReceived(self, data):
    self.buf = self.buf + data
    while len(self.buf) > 0:
      packet = self.readPacket()
      method, deferred, time = self.inflight[packet.seqNumber]
      del(self.inflight[packet.seqNumber])
      log.msg("Received response for %s: %s" % (packet.seqNumber, method))
      callback = getattr(self, "receive_%s" % method.replace(".", "_"), None)
      if callback == None:
        log.err("Unknown method: %s" % method)
        log.err("Words received: %s" % packet.words)
      else:
        callback(self, packet, deferred)

class FBClient(FBClientBase):
  loggedIn = False

  def adminSayAll(self, message):
    d = defer.Deferred()
    if self.loggedIn:
      packet = Packet(False, False, self.next_seq(), ["admin.say", message, "all"])
      self.writePacket(packet)
    else:
      d.errback("Must be logged in to perform this command.")
    return d

  def adminSayTeam(self, message, teamId):
    d = defer.Deferred()
    if self.loggedIn:
      packet = Packet(False, False, self.next_seq(), ["admin.say", message, "team", teamId])
      self.writePacket(packet, d)
    else:
      d.errback("Must be logged in to perform this command.")
    return d

  def adminSaySquad(self, message, teamId, squadId):
    d = defer.Deferred()
    if self.loggedIn:
      packet = Packet(False, False, self.next_seq(), ["admin.say", message, "squad", teamId, squadId])
      self.writePacket(packet, d)
    else:
      d.errback("must be logged in to perform this command.")
    return d

  def adminSayPlayer(self, message, playerName):
    d = defer.Deferred()
    if self.assertLoggedIn("adminSayPlayer"):
      packet = Packet(False, False, self.next_seq(), ["admin.say", message, "player", message])
      self.writePacket(packet)
    else:
      d.errback("Must be logged in to perform this command.")
    return d

  def serverInfo(self):
    d = defer.Deferred()
    server_info = Packet(False, False, self.next_seq(), ["serverInfo"])
    self.writePacket(server_info, d)
    return d

  def version(self):
    d = defer.Deferred()
    version = Packet(False, False, self.next_seq(), ["version"])
    self.writePacket(version, d)
    return d

  def login(self, password):
    od = defer.Deferred()
    d = defer.Deferred()
    login = Packet(False, False, self.next_seq(), ["login.hashed"])
    d.addCallback(lambda s: _loginHashed(h, password, od))
    d.addErrback(lambda e: od.errback(e))
    self.writePacket(login, d)
    return od

  def _loginHashed(self, hash, password, d):
    hashed = hash_pass(salt, password)
    login = Packet(False, False, self.next_seq(), ["login.hashed", hashed])
    self.writePacket(login, d)

  def receive_version(self, packet, d):
    version = " ".join(packet.words[1:])
    d.callback(version)

  def receive_serverInfo(self, packet, d):
    serverstate = ServerState()
    serverstate.serverName = packet.words[1]
    serverstate.playerCount = int(packet.words[2])
    serverstate.maxPlayers = int(packet.words[3])
    serverstate.gameMode = packet.words[4]
    serverstate.mapName = packet.words[5]
    serverstate.currentRound = int(packet.words[6])
    serverstate.totalRounds = packet.words[7]
    serverstate.numTeams = int(packet.words[8])
    numTeams = self.serverstate.numTeams
    serverstate.teamScores = []
    for i in range(self.serverstate.numTeams):
      serverstate.teamScores.append(int(packet.words[8+i+1]))
    serverstate.targetScores = int(packet.words[8+numTeams+1])
    serverstate.onlineState = packet.words[8+numTeams+2]
    serverstate.isRanked = packet.words[8+numTeams+3]
    serverstate.hasPunkbuster = packet.words[8+numTeams+4]
    serverstate.hasPassword  = packet.words[8+numTeams+5]
    serverstate.serverUptime = int(packet.words[8+numTeams+6])
    serverstate.roundTime = int(packet.words[8+numTeams+7])
    serverstate.joinAddress = packet.words[8+numTeams+8]
    serverstate.punkbusterVersion = packet.words[8+numTeams+9]
    serverstate.joinQueueEnabled = packet.words[8+numTeams+10]
    serverstate.region = packet.words[8+numTeams+11]
    serverstate.pingSite = packet.words[8+numTeams+12]
    serverstate.country = packet.words[8+numTeams+13]
    d.callback(serverstate)

  def receive_login_hashed(self, packet, d):
    rv = packet.words[0]
    if rv == u'InvalidPasswordHash':
      log.err("Invalid password hash")
      d.errback(rv)
      return

    if len(packet.words) > 1:
      salt = packet.words[1]
      d.callback(salt)
    else:
      self.loggedIn = True
      d.callback("OK")


class FBClientFactory(protocol.ClientFactory):
  protocol = FBClient
