import os
import binascii
import hashlib

def get_salt():
  """
  Returns a hex-encoded cryptographically secure random salt string.

  :return: Hex encoded string.
  """
  salt = os.urandom(16)
  return binascii.hexlify(salt).upper()

def hash_pass(salt, secret):
  """
  Given a salt and a secret, returns a hex-encoded MD5 hash of the two strings.

  :param salt:  string
  :param secret:  string
  :return: Hex encoded string.
  """
  g = hashlib.md5()
  g.update(binascii.unhexlify(salt) + secret.encode("ascii"))
  return g.hexdigest().upper()

def auth(salt, secret, input):
  """
  Given a salt, secret, and input hash, tests whether the input hash matches the
  hash of the salt and secret.

  :param salt:  string
  :param secret: string
  :param input: hex encoded string
  :return: Boolean
  """
  return hash_pass(salt, secret) == input.upper()
