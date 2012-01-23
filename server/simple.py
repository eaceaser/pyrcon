import json
import logging

from gevent import event
from gevent.server import StreamServer

logger = logging.getLogger("SimpleServer")
class SimpleJsonServer:
  def __init__(self, socket, address, control):
    self._socket = socket
    self._control = control

  #TODO: Switch from run to start
  def run(self):
    logger.info("Simple server started.")
    # Auth
    fileobj = self._socket.makefile()
    salt = self._control.get_salt()
    msg = { 'salt': salt }

    m = json.dumps(msg)
    logger.debug("Writing auth packet: %s" % m)
    fileobj.write(m)
    fileobj.write("\n")
    fileobj.flush()

    logger.debug("Waiting for auth response.")
    auth = fileobj.readline().rstrip()
    pw = json.loads(auth)['secret']
    logger.debug("Received secret: %s" % pw)

    if not self._control.auth(salt, pw):
      logger.debug("Authentication failed. Closing connection.")
      msg = { 'go away': True }
      fileobj.write(json.dumps(msg))
      fileobj.write("\n")
      fileobj.flush()
      fileobj.close()
      self._socket.close()
      return

    while True:
      line = fileobj.readline().rstrip()
      if line is None or line == "":
        logger.debug("Socket went away. Connection closed.")
        fileobj.close()
        self._socket.close()
        return

      logger.debug("Received line: %s" % line)
      try:
        j = json.loads(line)
        methodName = j["methodName"]
        arguments = []
        method = None

        if "arguments" in j:
          arguments = j["arguments"]

        if "server" in j and j["server"] == True:
          server = self._control.getServer()
          method = getattr(server, methodName)
        else:
          method = getattr(self._control, methodName)

        rv = method(*arguments)
        # for the sake of this simple server we just block.
        response = { 'response': rv.get() }
        responseStr = json.dumps(response)
        logger.debug("Sending response: %s" % json.dumps(response))
        fileobj.write(responseStr)
        fileobj.write("\n")
        fileobj.flush()
      except ValueError:
        logger.debug("Illegal command received. Throwing connection away.")
        fileobj.close()
        self._socket.close()

def simpleServer(control):
  handler = lambda socket, address: SimpleJsonServer(socket, address, control).run()
  server = StreamServer(('0.0.0.0', 31337), handler)
  server.start()
