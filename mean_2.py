import socket
import os
from _thread import *
import json
import uuid
import struct

message_length = 9
ServerSocket = socket.socket()
host = ""
port = 5003
try:
    ServerSocket.bind((host, port))
except socket.error as e:
    print(str(e))

print("Waitiing for a Connection..")
ServerSocket.listen(2000)

clients = {}


def send_to_client(sock, result):
    sock.send(struct.pack("!i", result))


def threaded_client(cliento, clientid):
    bufferobj = bytearray()
    start_index = 0
    while True:
        data = cliento.recv(1024)
        if data:
            for b in data:
                bufferobj.append(b)
                if len(bufferobj) % message_length == 0:
                    (instruction, timestamp, price) = struct.unpack(
                        "!cii", bufferobj[start_index : start_index + message_length]
                    )
                    instruction = instruction.decode('utf-8')
                    if clientid not in clients:
                        if instruction == "Q":
                            res = 0
                            send_to_client(cliento, res)
                        else:
                            clients[clientid] = [[instruction, (timestamp, price)]]
                            start_index += 9

                    else:
                        if instruction == "Q":
                            list_is = clients[clientid]
                            filterd = sorted(list_is, key=lambda s: s[1][0])
                            eligible_prices = [
                                i
                                for i in filterd
                                if i[1][0] >= timestamp and i[1][0] <= price
                            ]
                            tot = 0
                            for pprice in eligible_prices:
                                tot += pprice[1][1]
                            if len(eligible_prices) == 0:
                                res = 0
                            else:
                                res = tot // len(eligible_prices)

                            start_index += message_length
                            send_to_client(cliento, res)
                        else:
                            if instruction == "I":
                                clients[clientid].append(
                                    [instruction, (timestamp, price)]
                                )
                                start_index += message_length
                            else:
                                print("bad data")
                                print(bufferobj[start_index])
        if not data:
            cliento.close()
            break


while True:
    Client, address = ServerSocket.accept()
    client_id = uuid.uuid4()
    start_new_thread(threaded_client, (Client, client_id))
ServerSocket.close()
