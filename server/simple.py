import json
import logging

from gevent import event
from gevent.server import StreamServer

logger = logging.getLogger("SimpleServer")
class SimpleJsonServer:
  def __init__(self, socket, address, control):
    self._socket = socket
    self._control = control

  def run(self):
    logger.info("Simple server started.")
    # Auth
    fileobj = self._socket.makefile()
    salt = self._control.getSalt()
    msg = { 'salt': salt }

    fileobj.write(json.dumps(msg))
    fileobj.write("\n")
    fileobj.flush()

    auth = fileobj.readline().rstrip()
    pw = json.loads(auth)['secret']

    if not self._control.auth(salt, pw):
      msg = { 'go away': True }
      fileobj.write(json.dumps(msg))
      fileobj.write("\n")
      fileobj.flush()
      fileobj.close()
      self._socket.close()
      return

    while True:
      line = fileobj.readline().rstrip()
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
      except ValueError:
        self._socket.send("blah!\n")
      fileobj.flush()

def simpleServer(control):
  handler = lambda socket, address: SimpleJsonServer(socket, address, control).run()
  server = StreamServer(('0.0.0.0', 31337), handler)
  server.serve_forever()
