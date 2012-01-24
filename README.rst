PyRCon
============

PyRCon is a Frostbite Engine 2 RCon proxy server that is intended to be a replacement for Procon.

Documentation
-------------
http://eaceaser.github.com/pyrcon

Goals
-----

* Support Battlefield 3
* Provide an easy platform to write event-driven modules to add functionality to a BF3 Server.
* Be crossplatform.
* Be lightweight and easily configurable.

Requirements
------------
* Python 2.7
* gevent (http://www.gevent.org)
* PyYAML (http://pyyaml.org)

Installation
------------
Currently PyRCon is installed by installing its dependencies and cloning the git repository.

::

  pip install gevent
  pip install pyyaml
  git clone git://github.com/eaceaser/pyrcon.git

Configuration
-------------
A sample configuration file is included at ``config/sample.yml``. Edit the file to your heart's content.

Running the Server
------------------
Currently the server does not daemonize itself. That is coming soon.

::

  ./pyrcon.py -c path_to_config.yml

It is recommended to run with ``-vv`` for debug output.

Running the Client
------------------
Currently, PyRCon's client/server authentication model is very simple. Configure a password in your configuration file, and
then run:

::

  ./pyrconc.py -P PASSWORD

Client Example
--------------
An example of the client usage:

::

  PyRCon> help
  usage: info: Basic Server Info.
  usage: maps
  usage: version: BF3 Server Version.
  usage: vars
  usage: player
  usage: ban
  usage: nextround: Switch server to the next round.
  usage: knownmaps
  usage: teams
  PyRCon> version
  BF3 896646
  PyRCon> maps
  PyRCon/maps> list
  (* = Current Map, ! = Next Map)
  *1. MP_Subway RushLarge0  2
  !2. XP1_003 RushLarge0  2
   3. MP_001  RushLarge0  2
   4. XP1_001 RushLarge0  2
   5. MP_003  RushLarge0  2
   6. MP_007  RushLarge0  2
   7. MP_017  RushLarge0  2
   8. MP_013  RushLarge0  2
   9. MP_012  RushLarge0  2
   10. MP_011 RushLarge0  2
   11. XP1_002  RushLarge0  2
   12. XP1_004  RushLarge0  2
   13. MP_018 RushLarge0  2

  PyRCon/maps>

The client has full readline support, including command history and tab completion.

General Roadmap
-------
* Finish pyrconc client
* Finish documentation.
* Add unit testing.
* Remove the simple JSON protocol and replace it with a strutured protobuf-driven protocol.
* Start a separate web frontend project for PyRCon.
* Rewrite the authentication to support multi-user credentials.
* Add SSL cert based authentication.

Authors
-------
Edward Ceaser eac@tehasdf.com
