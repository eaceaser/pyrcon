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

Installation and Quick Start (Linux/Mac OS X)
------------
First make sure you have a working Python environment. For example:

::

  terminal> python
  Python 2.7.2 (default, Dec 20 2011, 16:56:46) 
  [GCC 4.2.1 (Based on Apple Inc. build 5658) (LLVM build 2336.1.00)] on darwin
  Type "help", "copyright", "credits" or "license" for more information.
  >>> 

Currently the easiest way to install PyRCon is to clone the git repo. 

::

  git clone git://github.com/eaceaser/pyrcon.git

Alternatively, you can download the current snapshot of the source tree from github: https://github.com/eaceaser/pyrcon/zipball/master

Next, install the python dependencies:

::

  pip install gevent
  pip install pyyaml

I prefer using ``pip``, but ``easy_install`` should work just fine too.

Finally, edit the sample config file located in ``pyrcon/config/sample.yml``. Most importantly, edit the rcon section:

::

  rcon:
    host: YOUR_BF3_SERVER_HOST
    port: YOUR_BF3_SERVER_RCON_PORT
    password: YOUR_BF3_SERVER_RCON_PASSWORD

As well as the server section:

::

  server:
    password: SOME_PYRCON_PASSWORD

Save your configuration file to a new file, for example, ``config.yml``.

Finally, run PyRCon:

::

  python ./pyrcon.py -c config/config.yml -vv

It is recommended to run with the -vv (verbose) flags as things are currently unstable.

Running the Client
------------------
To run the command line client, run:

::

  term> python pyrconc.py -P SOME_PYRCON_PASSWORD

You should be given a ``PyRCon>`` prompt which you can use to interact with the server. For example:

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
  PyRCon> knownmaps
  Operation Metro (MP_Subway): ConquestLarge0 ConquestSmall0 RushLarge0 SquadRush0 TeamDeathMatch0 SquadDeathMatch0
  Sharqi Peninsula (XP1_003): ConquestLarge0 ConquestSmall0 ConquestSmall1 RushLarge0 SquadRush0 TeamDeathMatch0 SquadDeathMatch0
  Grand Bazaar (MP_001): ConquestLarge0 ConquestSmall0 RushLarge0 SquadRush0 TeamDeathMatch0 SquadDeathMatch0
  Strike at Karkand (XP1_001): ConquestLarge0 ConquestSmall0 ConquestSmall1 RushLarge0 SquadRush0 TeamDeathMatch0 SquadDeathMatch0
  Tehran Highway (MP_003): ConquestLarge0 ConquestSmall0 RushLarge0 SquadRush0 TeamDeathMatch0 SquadDeathMatch0
  ...
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

Why not Procon?
---------------

* Procon is not easy to run crossplatform. It currently relies on having the .NET CLR installed in some form. Most
non-Windows servers do not have a CLR environment unless they install Mono, which is not a common package on most
server OS distributions. 
* Procon is not very lightweight or componentized. It is both a layer server as well as a GUI that includes features 
such as a map viewer, plugin downloader, etc. I think a more modular architecture where the server is a headless,
daemonizable process with no UI provides for a more flexible and easier to manage system.
* Easier Plugin / Module API. Procon handles plugins by using a very strange C# runtime compilation stage, which makes 
writing and testing plugins very difficult. 

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
