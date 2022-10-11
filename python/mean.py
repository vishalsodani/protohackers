import socket
import os
from _thread import *
import json
import uuid


message_length = 9
ServerSocket = socket.socket()
host = ""
port = 5003
ThreadCount = 0
try:
    ServerSocket.bind((host, port))
except socket.error as e:
    print(str(e))

print("Waitiing for a Connection..")
ServerSocket.listen(2000)

clients = {}


def threaded_client(cliento, clientid):
    client_data = []
    start_index = 0
    while True:
        data = cliento.recv(1024)
        if data:
            for b in data:
                client_data.append(b)
                # print("clientid:%s start index %s" % (clientid,start_index))
                if len(client_data) % 9 == 0:
                    instruction = client_data[start_index]
                    timestamp = int.from_bytes(
                        bytearray(client_data[start_index + 1 : start_index + 5]),
                        "big",
                        signed=True,
                    )
                    price = int.from_bytes(
                        bytearray(client_data[start_index + 5 : start_index + 9]),
                        "big",
                        signed=True,
                    )
                    if clientid not in clients:
                        if chr(client_data[start_index]) == "Q":
                            res = 0
                            cliento.send(res.to_bytes(4, byteorder="big", signed=True))
                        else:
                            clients[clientid] = [[instruction, (timestamp, price)]]
                            start_index += 9
                            print(clients)

                    else:
                        if chr(client_data[start_index]) == "Q":
                            print("sending")
                            # print(client_data[start_index:start_index+9])
                            print("start at %s" % start_index)
                            list_is = clients[clientid]
                            # print(list_is)
                            filterd = sorted(list_is, key=lambda s: s[1][0])
                            # print("filtered %s" % filterd)
                            eligible_prices = [
                                i
                                for i in filterd
                                if i[1][0] >= timestamp and i[1][0] <= price
                            ]
                            tot = 0
                            # print("eligible %s" % eligible_prices)
                            for pprice in eligible_prices:
                                tot += pprice[1][1]
                            print("total %s" % tot)
                            print("len of eleigble %s" % len(eligible_prices))
                            # print("range %s, %s" % (timestamp,price))
                            print("--debug sending----------")
                            if len(eligible_prices) == 0:
                                res = 0
                            else:
                                res = tot // len(eligible_prices)

                            start_index += 9
                            cliento.send(res.to_bytes(4, byteorder="big", signed=True))
                        else:
                            if chr(client_data[start_index]) == "I":
                                clients[clientid].append(
                                    [instruction, (timestamp, price)]
                                )
                                start_index += 9
                                # print("exists")
                                # print(clients)
                                # print("exists updated")
                            else:
                                print("bad data")
                                print(client_data[start_index])
        if not data:
            cliento.close()
            break


while True:
    Client, address = ServerSocket.accept()
    print("Connected to: " + address[0] + ":" + str(address[1]))
    client_id = uuid.uuid4()
    start_new_thread(threaded_client, (Client, client_id))
    ThreadCount += 1
    print("Thread Number: " + str(ThreadCount))
ServerSocket.close()
