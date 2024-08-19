# ChordProtocol
A simple Python implementation of the Chord p2p protocol.

### Usage:
To launch a node one must pass it an IP address and Port number as arguments

`python node.py <ip> <port>`

To add a node to the Chord ring, provide the IP and Port number of a known node and the IP address and Port number of the new node.

`python node.py <known_ip> <known_port> <ip> <port>`

Todo:
* implement leave (nodes can leave but not by menu input)
* implement key/value pairs (adding data to nodes)
* fix finger table (implement look ahead)

Done:
* start
* stabalize
* fix fingers
* notify 
* join
* find successor
* find predecessor
* closest proceding node
* check predecessor
