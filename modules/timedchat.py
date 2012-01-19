from eventhandler import EventHandler

import gevent

class TimedChat(EventHandler):
  def __init__(self, control, config):
    self._control = control
    self._config = config

    for message in config:
      interval = message["interval"]
      text = message["text"]
      gevent.spawn(self._say_on_interval, interval, text)

  def _say_on_interval(self, interval, text):
    while True:
      self._control.server().say_all(text)
      gevent.sleep(interval)

module = TimedChat
