import socket
import os
import subprocess
import pickle

s = socket.socket()
host = '192.168.1.7'
port = 10000
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
    if temp[0] == 'shutdown':
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        exit()
    m = pickle.dumps(['up'])
    s.send(m)
