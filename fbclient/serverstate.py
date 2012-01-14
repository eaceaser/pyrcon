class ServerState:
  def __init__(self):
    self.__dict__ = {}

  def __getattr__(self, i):
    if i in self.__dict__:
      return self.__dict__[i]
    else:
      raise AttributeError, i

  def __setattr__(self, i, v):
    if i in self.__dict__:
      self.__dict__[i] = v
    else:
      self.__dict__.update({i:v})
    return v

  def __str__(self):
    return "%s" % self.__dict__
