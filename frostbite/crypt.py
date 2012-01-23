import os
import binascii
import hashlib

def get_salt():
  salt = os.urandom(16)
  return binascii.hexlify(salt).upper()

def hash_pass(salt, secret):
  g = hashlib.md5()
  g.update(binascii.unhexlify(salt) + secret.encode("ascii"))
  return g.hexdigest().upper()

def auth(salt, secret, input):
  return hash_pass(salt, secret) == input.upper()
