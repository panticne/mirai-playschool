""" This file is used from a player to establish a connection with the game server"""

__author__ = "Nemanja Pantic"
__copyright__ = "Copyright 2020, HEIG-VD"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "nemanja.pantic@heig-vd.ch"
import socket
import pickle

s = socket.socket()
# Change IP here
host = '192.168.1.7'
port = 10000
# We check if the server is up
try:
    s.connect((host, port))
except:
    print("The server is down")
while True:
    try:
        data = s.recv(1024)
        temp = pickle.loads(data)
    except:
        print("Server disconnected")
        exit()

    # When received by the server, we kill the application
    if temp[0] == 'shutdown':
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        exit()
    m = pickle.dumps(['up'])
    s.send(m)
