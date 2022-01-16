#!/usr/bin/env python

"""
+-----------------------+
|                       |                           +----------------------------+
|        Conn           +---------------------------+.ID                         |
|                       |                           |.write(Message {...} )      |
+----------+------------+                           |.ask  (Message {...} )      |
           |                                        +----------------------------+
           |                                        |.close   ()                 |
           |                                        |.isClosed()                 |
           |                                        +----------------------------+
           +----------------------+                 |.waitServerConnect()        |
           |.connect("namespace") |                 |.namespace    ("namespace") |
           +-----+----------------+                 |.disconnectAll()            |
                 |                                  +----------------------------+
                 |
                 |
                 |                                                                      +--------------------------+
           +-----+----------------+                                                     | Message {                |
           |                      |                 +----------------------------+      |                          |
           |       NSConn         +-----------------+.emit("event", body)        +------+  Namespace: "namespace", |
           |                      |                 +----------------------------+      |  Event:     "event",     |
           +-----+----------------+                 |.disconnect()               |      |  Body:      body,        |
                 |                                  +----------------------------+      |                          |
                 |                                  |.ask     ("event", body)    |      | }                        |
                 |                                  |.room    ("roomName")       |      +--------------------------+
                 +----------------------+           |.rooms                      |
                 |.joinRoom("roomName") |           |.leaveAll()                 |
                 +-------+--------------+           +----------------------------+
                         |
                         |
                         |                                                              +--------------------------+
                         |                                                              | Message {                |
                 +-------+--------------+                                               |                          |
                 |                      |           +----------------------------+      |  Namespace: "namespace", |
                 |         Room         +-----------+.emit("event", body)        +------+  Room:      "roomName",  |
                 |                      |           +----------------------------+      |  Event:     "event",     |
                 +----------------------+           |.leave()                    |      |  Body:      body,        |
                                                    +----------------------------+      |                          |
                                                                                        | }                        |
                                                                                        +--------------------------+

"""
import sys
from .neff import IRISSocket, Conn, NSConn, Room, Message, NeffSupportSocket, Bolors
if sys.version_info < (3, 5):
    raise EnvironmentError("Python 3.5 or above is required")
__version__ = "0.5.1"

__all__ = [
    '__version__',
    'IRISSocket',
    'NeffSupportSocket',
    'Conn',
    'NSConn',
    'Room',
    'Message',
    'Bolors',
]
