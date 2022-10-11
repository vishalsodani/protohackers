import socket
import os
from _thread import *
import json
import uuid
import shlex

ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
host = ""
port = 5003
ThreadCount = 0
try:
    ServerSocket.bind((host, port))
except socket.error as e:
    print(str(e))


clients = {}


while True:
    data, address = ServerSocket.recvfrom(4096)
    data = data.decode("utf-8")
    if "=" in data:
        d = data.split("=", 1)
        if d[0] == "version":
            pass
        else:
            if d[0] not in clients:
                clients[d[0]] = d[1]
            else:
                clients.update({d[0]: d[1]})
    else:
        if data == "version":
            sent = ServerSocket.sendto(
                bytes("version" + "=" + "Its Mumbais UDP", "utf-8"), address
            )
        if data in clients:
            message = clients[data]
            sent = ServerSocket.sendto(bytes(data + "=" + message, "utf-8"), address)
        else:
            sent = ServerSocket.sendto(bytes(data + "=", "utf-8"), address)
