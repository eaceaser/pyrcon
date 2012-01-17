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
        method = getattr(self._control, methodName)
        rv = method()
        response = { 'methodName': methodName, 'response': rv }
        fileobj.write(json.dumps(response))
        fileobj.write("\n")
      except ValueError:
        self._socket.send("blah!\n")
      fileobj.flush()

def simpleServer(control):
  handler = lambda socket, address: SimpleJsonServer(socket, address, control).run()
  server = StreamServer(('0.0.0.0', 31337), handler)
  server.serve_forever()
