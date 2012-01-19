from eventhandler import EventHandler

import gevent

class TimedChat(EventHandler):
  def __init__(self, control, config):
    self._control = control
    self._config = config

    for message in config:
      interval = message["interval"]
      text = message["text"]
      delay = message.get("delay", 0)

      gevent.spawn(self._say_on_interval, interval, delay, text)

  def _say_on_interval(self, interval, delay, text):
    if delay > 0:
      gevent.sleep(delay)

    while True:
      self._control.server().say_all(text)
      gevent.sleep(interval)

module = TimedChat
