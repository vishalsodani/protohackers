import socket
import os
from _thread import *

ServerSocket = socket.socket()
host = ""
port = 5004
ThreadCount = 0
try:
    ServerSocket.bind((host, port))
except socket.error as e:
    print(str(e))

print("Waitiing for a Connection..")
ServerSocket.listen(10)


def threaded_client(connection):
    while True:
        data = connection.recv(2048)
        if not data:
            break
        connection.send(data)
    connection.close()


while True:
    Client, address = ServerSocket.accept()
    print("Connected to: " + address[0] + ":" + str(address[1]))
    start_new_thread(threaded_client, (Client,))
    ThreadCount += 1
    print("Thread Number: " + str(ThreadCount))
ServerSocket.close()
