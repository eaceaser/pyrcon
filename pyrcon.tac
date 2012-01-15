import io

from yaml import load, dump
from yaml import CLoader as Loader, CDumper as Dumper

from twisted.application import internet, service
from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic

from frostbite import client

config = io.open("config.yml")

data = load(config, Loader=Loader)
print data

hostname = data['host']
port = data['port']
password = data['password']

application = service.Application("pyrcon")
collection = service.IServiceCollection(application)
fbclient = internet.TCPClient(hostname, port, client.FBClientFactory()).setServiceParent(collection)

config.close()
