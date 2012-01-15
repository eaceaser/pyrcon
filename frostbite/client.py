import time
import logging

import gevent.pool
from gevent.event import AsyncResult
from gevent import socket, queue

from frostbite.serverstate import ServerState
from frostbite.packet import Packet

import hashlib

logger = logging.getLogger("FBClient")
logging.basicConfig(level=logging.DEBUG)
def hash_pass(salt, password):
  m = hashlib.md5()
  decoded = salt.decode('hex')
  m.update(decoded+password.encode("ascii"))
  return m.hexdigest()

class FBClient:
  seq = 0

  def __init__(self, hostname, port):
    self.hostname = hostname
    self.port = port
    self._socket = None
    self._send_queue = gevent.queue.Queue()
    self._read_queue = gevent.queue.Queue()
    self._inflight = {}
    self._group = gevent.pool.Group()

  def start(self):
    address = (socket.gethostbyname(self.hostname), self.port)
    logger.info("Connecting to %r" % (address,))
    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self._socket.connect(address)
    self._group.spawn(self._send_loop)
    self._group.spawn(self._read_loop)
    self._group.spawn(self._process_loop)

  def _next_seq(self):
    seq = self.seq
    self.seq = self.seq + 1
    return seq

  def _write(self, packet):
    self._send_queue.put(packet)

  def _send_loop(self):
    while True:
      packet = self._send_queue.get()
      logger.debug("Writing packet inflight: %s %s" % (packet.seqNumber, packet.words))
      self._socket.sendall(packet.encode())

  def _read_loop(self):
    buf = ''
    while True:
      data = self._socket.recv(512)
      buf += data
      while len(buf) > Packet.processSize:
        packet, buf = Packet.decode(buf)
        logger.debug("Received data and decoded a packet.")
        self._read_queue.put(packet)

  def _process_loop(self):
    #login shit
    while True:
      packet = self._read_queue.get()
      self._handle(packet)

  def _handle(self, packet):
    filt, response = self._inflight[packet.seqNumber]
    if response is not None:
      del(self._inflight[packet.seqNumber])
      gevent.spawn(filt, packet).link(response)
      logger.debug("Received response for %s: %s" % (packet.seqNumber, packet))
    else:
      logger.err("Message received for an unknown sequence: %s", (packet.seqNumber))

  def stop(self):
    self._group.kill()
    if self._socket is not None:
      self._socket.close()
      self._socket = None

  def join(self):
    self._group.join()

  def send(self, command):
    response = AsyncResult()
    packet = command.toPacket(self._next_seq())
    self._inflight[packet.seqNumber] = (command.filter, response)
    self._send_queue.put(packet)
    return response

#class FBClient(FBClientBase):
#  loggedIn = False
#
#  def adminSayAll(self, message):
#    d = defer.Deferred()
#    if self.loggedIn:
#      packet = Packet(False, False, self._next_seq(), ["admin.say", message, "all"])
#      self.writePacket(packet)
#    else:
#      d.errback("Must be logged in to perform this command.")
#    return d
#
#  def adminSayTeam(self, message, teamId):
#    d = defer.Deferred()
#    if self.loggedIn:
#      packet = Packet(False, False, self._next_seq(), ["admin.say", message, "team", teamId])
#      self.writePacket(packet, d)
#    else:
#      d.errback("Must be logged in to perform this command.")
#    return d
#
#  def adminSaySquad(self, message, teamId, squadId):
#    d = defer.Deferred()
#    if self.loggedIn:
#      packet = Packet(False, False, self._next_seq(), ["admin.say", message, "squad", teamId, squadId])
#      self.writePacket(packet, d)
#    else:
#      d.errback("must be logged in to perform this command.")
#    return d
#
#  def adminSayPlayer(self, message, playerName):
#    d = defer.Deferred()
#    if self.assertLoggedIn("adminSayPlayer"):
#      packet = Packet(False, False, self._next_seq(), ["admin.say", message, "player", message])
#      self.writePacket(packet)
#    else:
#      d.errback("Must be logged in to perform this command.")
#    return d
#
#  def serverInfo(self):
#    d = defer.Deferred()
#    server_info = Packet(False, False, self.next_seq(), ["serverInfo"])
#    self.writePacket(server_info, d)
#    return d
#
#  def login(self, password):
#    od = defer.Deferred()
#    d = defer.Deferred()
#    login = Packet(False, False, self.next_seq(), ["login.hashed"])
#    d.addCallback(lambda s: _loginHashed(h, password, od))
#    d.addErrback(lambda e: od.errback(e))
#    self.writePacket(login, d)
#    return od
#
#  def _loginHashed(self, hash, password, d):
#    hashed = hash_pass(salt, password)
#    login = Packet(False, False, self.next_seq(), ["login.hashed", hashed])
#    self.writePacket(login, d)
#
#  def receive_version(self, packet, d):
#    version = " ".join(packet.words[1:])
#    d.callback(version)
#
#  def receive_serverInfo(self, packet, d):
#    serverstate = ServerState()
#    serverstate.serverName = packet.words[1]
#    serverstate.playerCount = int(packet.words[2])
#    serverstate.maxPlayers = int(packet.words[3])
#    serverstate.gameMode = packet.words[4]
#    serverstate.mapName = packet.words[5]
#    serverstate.currentRound = int(packet.words[6])
#    serverstate.totalRounds = packet.words[7]
#    serverstate.numTeams = int(packet.words[8])
#    numTeams = self.serverstate.numTeams
#    serverstate.teamScores = []
#    for i in range(self.serverstate.numTeams):
#      serverstate.teamScores.append(int(packet.words[8+i+1]))
#    serverstate.targetScores = int(packet.words[8+numTeams+1])
#    serverstate.onlineState = packet.words[8+numTeams+2]
#    serverstate.isRanked = packet.words[8+numTeams+3]
#    serverstate.hasPunkbuster = packet.words[8+numTeams+4]
#    serverstate.hasPassword  = packet.words[8+numTeams+5]
#    serverstate.serverUptime = int(packet.words[8+numTeams+6])
#    serverstate.roundTime = int(packet.words[8+numTeams+7])
#    serverstate.joinAddress = packet.words[8+numTeams+8]
#    serverstate.punkbusterVersion = packet.words[8+numTeams+9]
#    serverstate.joinQueueEnabled = packet.words[8+numTeams+10]
#    serverstate.region = packet.words[8+numTeams+11]
#    serverstate.pingSite = packet.words[8+numTeams+12]
#    serverstate.country = packet.words[8+numTeams+13]
#    d.callback(serverstate)
#
#  def receive_login_hashed(self, packet, d):
#    rv = packet.words[0]
#    if rv == u'InvalidPasswordHash':
#      log.err("Invalid password hash")
#      d.errback(rv)
#      return
#
#    if len(packet.words) > 1:
#      salt = packet.words[1]
#      d.callback(salt)
#    else:
#      self.loggedIn = True
#      d.callback("OK")
