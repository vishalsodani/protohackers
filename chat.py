import socket
import os
from _thread import *
import json
import uuid


message_length = 9
ServerSocket = socket.socket()
host = ""
port = 5004
ThreadCount = 0
try:
    ServerSocket.bind((host, port))
except socket.error as e:
    print(str(e))

print("Waitiing for a Connection..")
ServerSocket.listen(2000)

clients = {}
d = 0


def send_new_joinee(client, name):
    for c in clients.keys():
        if c == client:
            pass
        else:
            # print(clients[c])
            if clients[c]["name"] != "":
                print("join announcement")
                print("* %s has entered the room" % name)
                sock = clients[c]["socket"]
                print("sending to %s" % clients[c]["name"])
                sock.send(bytes("* %s has entered the room\n" % name.strip(), "utf-8"))


def send_msg_to_new_user(sock, clientid):
    all_users = "* The room contains: %s\n"
    other_users = []
    for c in clients.keys():
        if c == clientid:
            pass
        else:
            if len(clients[c]["name"]) != 0:
                other_users.append(clients[c]["name"].strip())
    # print("----------------")
    # print(other_users)
    # print("-----processed-----------")
    ", ".join(other_users)
    # print("send all")
    sock.send(bytes(all_users % other_users, "utf-8"))


def send_chat_message(message, user, clientid):
    msg = "[%s] %s" % (user, message)
    print("ready to send %s" % msg)
    for c in clients.keys():
        if c == clientid:
            pass
        else:
            if len(clients[c]["name"]) != 0:
                sock = clients[c]["socket"]
                sock.send(bytes(msg, "utf-8"))


def send_leave_message(user, clientid):
    msg = "* %s has left the room\n" % user.strip()
    # print("leaving %s" % user)
    if user == "":
        return
    for c in clients.keys():
        if c == clientid:
            pass
        else:
            if len(clients[c]["name"]) != 0:
                sock = clients[c]["socket"]
                # print("leaving %s send message to %s" % (user, clients[c]['name']))
                try:
                    sock.send(bytes(msg, "utf-8"))
                except:
                    pass


def threaded_client(cliento, clientid):
    client_data = ""
    start_index = 0
    clients[clientid] = {"name": "", "msgcount": 0, "socket": cliento}
    cliento.send(bytes("Welcome to budgetchat! What shall I call you?\n", "utf-8"))

    while True:
        data = cliento.recv(2)
        client_data += data.decode("utf-8")
        if client_data.endswith("\n"):
            if clientid in clients and clients[clientid]["msgcount"] == 0:
                e = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                n = client_data.strip()
                legal = all(c in e for c in n)
                if legal == False:
                    cliento.send(bytes("naughty potty", "utf-8"))
                    clients.pop(clientid)
                    cliento.close()
                    break
                clients[clientid] = {
                    "name": client_data.strip(),
                    "msgcount": 1,
                    "socket": cliento,
                }
                # print("sending presence")
                print(client_data)
                send_new_joinee(clientid, client_data.strip())
                send_msg_to_new_user(cliento, clientid)
                client_data = ""
            else:
                print("message send for chat")
                print(client_data)
                print(clients[clientid]["name"])
                print("end message")
                send_chat_message(client_data, clients[clientid]["name"], clientid)
                client_data = ""
                # pass
                # send_new_joinee(clientid, client_data.strip())
        if not data:
            if clients[clientid]["name"] != "":
                send_leave_message(clients[clientid]["name"], clientid)
            cliento.close()
            clients.pop(clientid)
            break


while True:
    Client, address = ServerSocket.accept()
    # print("Connected to: " + address[0] + ":" + str(address[1]))
    client_id = uuid.uuid4()
    start_new_thread(threaded_client, (Client, client_id))
    ThreadCount += 1
    # print("Thread Number: " + str(ThreadCount))
ServerSocket.close()
