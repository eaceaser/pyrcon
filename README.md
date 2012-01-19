# PyRCon

PyRCon is a Frostbite Engine RCon proxy server that is intended to be a replacement for procon. 

Goals:

- Support Battlefield 3
- Provide an easy platform to write event-driven modules to add functionality to a BF3 server.
- Be crossplatform.
- Be lightweight and easily configurable.

# Requirements

- Python 2.7
- gevent (http://www.gevent.org/)
- PyYAML (http://pyyaml.org/)

# Architecture

PyRCon is designed as a service layer that provides additional functionality to clients on top of what
is exposed by the Frostbite engine's RCon protocol. The PyRCon server connects to a configured BF3
server, and then exposes endpoints that clients can connect to to control PyRCon and the underlying
game server.

The only current endpoint is a very simple json protocol that is used by the proof-of-concept pyrconc
client, included in this project.

# TODO

- Finish pyrconc client
- Implement event driven module API
- Write some modules.
- Add tests and docstrings.
- Use @properties.
- Add a procon-compatible layer server so procon and its various tools can connect to pyrcon.
- Remove the simple JSON protocol and replace it with a structured protobuf-driven protocol.
- Refactor server and client to reduce boilerplate.
- Create a web frontend for pyrcon (a separate project that speaks this new protocol.)
- Add multi-user authentication.
- Add SSL cert based authentication.

# Authors

Edward Ceaser <eac@tehasdf.com>
