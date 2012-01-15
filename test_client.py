#!/usr/bin/env python2
import argparse
import sys

from frostbite import client
from frostbite import commands

parser = argparse.ArgumentParser(description="Test Frostbite RCon Client.")
parser.add_argument('-H', '--hostname', dest='hostname', help='Server Hostname', required=True)
parser.add_argument('-p', '--port', dest='port', help='Server Port', type=int, default=47200)
parser.add_argument('-P', '--password', dest='password', help='Server Password', required=True)
#parser.add_argument('-s', '--say', dest='message', help='Send an admin message')
args = parser.parse_args()

client = client.FBClient(args.hostname, args.port)
client.start()
response = client.send(commands.Version())

print response.get()

response = client.send(commands.ServerInfo()) 
print response.get()

response = client.send(commands.Login(args.password))
print response.get()

response = client.send(commands.AdminSay("hello there"))
print response.get()
