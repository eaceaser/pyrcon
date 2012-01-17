import json
import logging

from gevent.server import StreamServer

logger = logging.getLogger("SimpleServer")
class SimpleJsonServer:
  def __init__(self, socket, address, control):
    self._socket = socket
    self._control = control

  def run(self):
    logger.info("Simple server started.")
    fileobj = self._socket.makefile()
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

        if "serverName" in j:
          serverName = j["serverName"]
          server = self._control.getServer(serverName)
          method = getattr(server, methodName)
        else:
          method = getattr(self._control, methodName)

        rv = method(*arguments)
        response = { 'response': rv }
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
