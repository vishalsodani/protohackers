import socket
import os
from _thread import *
import json


def is_prime(n):
    if isinstance(n, float) and not n.is_integer():
        return False
    if n <= 1:
        return False
    if n == 2:
        return True
    if n == 3:
        return True
    if n % 2 == 0:
        return False
    if n % 3 == 0:
        return False

    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6

    return True


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


def threaded_client(cliento):
    client_data = ""
    while True:
        # client_data = ''
        data = cliento.recv(8)
        if data:
            print(data)
            client_data += data.decode("utf-8")

        if client_data.endswith("\n"):
            # print(client_data)
            data2 = client_data
            error = False
            client_data = ""
            try:
                dd1 = data2.splitlines()
                for dd2 in dd1:
                    dd = json.loads(dd2)
                    print(dd)
                    for field in ["method", "number"]:
                        if field not in dd:
                            error = True
                        if dd["method"] != "isPrime":
                            error = True
                    try:
                        if type(dd["number"]) == type(False):
                            error = True
                        else:
                            int(dd["number"])
                    except:
                        error = True
                    if error:
                        # client.send(bytes(dd,'utf-8'))
                        res = json.dumps({"hod": "isPrime", "error": False})
                        cliento.send(bytes(res + "\n", "utf-8"))
                        # break
                    # client.close()
                    else:
                        answer = is_prime(dd["number"])
                        res = json.dumps({"method": "isPrime", "prime": answer})
                        cliento.sendall(bytes(res + "\n", "utf-8"))

            except:
                import traceback

                # traceback.print_exc()
                # print("--------------------------")
                # print(data2)
                # print("--------------------------")
                res = json.dumps({"prime": False})
                cliento.send(bytes(res, "utf-8"))
                break
                # client.close()
        # client_data = ''
        # cliento.close()
        # connection.send(data)
    cliento.close()


while True:
    Client, address = ServerSocket.accept()
    print("Connected to: " + address[0] + ":" + str(address[1]))
    start_new_thread(threaded_client, (Client,))
    ThreadCount += 1
    print("Thread Number: " + str(ThreadCount))
ServerSocket.close()
