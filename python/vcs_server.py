import asyncio
from asyncore import read
import logging
from asyncio import StreamReader, StreamWriter
import struct
import json
import uuid
from datetime import datetime
from random import randint
from random import choice
from typing import Set
from queue import PriorityQueue
import heapq
import os
import hashlib

queues = {}
excluded = set()
working_q = {}
waiting_clients = []
deleted_job = []

counter = {}


def my_rand(start: int, end: int, exclude_values: Set[int] = None):
    if (
        not exclude_values
    ):  # in this case, there are no values to exclude so there is no point in filtering out any
        return randint(start, end)
    return choice(list(set(range(start, end)).difference(exclude_values)))


async def send_response(writer, res):
    writer.write(bytes(json.dumps(res) + "\n", "utf=8"))
    await writer.drain()


class ServerState:
    def __init__(self):
        self._writers = []

    async def add_client(
        self, reader: StreamReader, writer: StreamWriter, client_id
    ):  # A
        self._writers.append([writer, client_id])
        asyncio.create_task(self._echo(reader, writer, client_id))

    async def _echo(self, reader: StreamReader, writer: StreamWriter, client_id):  # C
        writer.write(bytes("READY\n", "utf=8"))
        await writer.drain()
        while data := await reader.readline():
            #print(counter)
            data = data.decode("utf-8").strip()
            if data == 'HELP':
                writer.write(bytes("READY\n", "utf=8"))
                await writer.drain()
            if data[0:3] == 'PUT':
                remaining_c = data[5:].split(' ')
                file_name = remaining_c[0]
                file_length = int(remaining_c[1])
                ofl = file_length
                data_is = ''
                revision = 1
                try:
                    os.makedirs(os.path.dirname(file_name), exist_ok=False)
                except:
                    pass
                with open(file_name, 'wb') as f:
                        while file_length > 0:
                            content = await reader.readline()
                            f.write(content)
                            data_is += content.decode("utf-8")
                            file_length -= len(content)

                if file_name not in counter:
                    counter[file_name] = {'r1':[ofl, hashlib.md5(data_is.encode("utf-8")).hexdigest(), data_is]}
                    writer.write(bytes(f"OK r{revision}\n", "utf=8"))
                    await writer.drain()
                    writer.write(bytes("READY\n", "utf=8"))
                    await writer.drain()
                else:
                    new_hash = hashlib.md5(data_is.encode("utf-8")).hexdigest()
                    # if counter[file_name][1] != file_length:
                    #     counter[file_name][0] += 1
                    #     counter[file_name][1] = file_length
                    last_key = len(counter[file_name].keys())
                    
                    if new_hash != counter[file_name][f'r{last_key}'][1]:
                        counter[file_name][f'r{last_key+1}'] = [ofl, new_hash, data_is]
                        revision = last_key + 1
                        #print(file_name)
                        #print(revision)
                        writer.write(bytes(f"OK r{revision}\n", "utf=8"))
                        await writer.drain()
                        writer.write(bytes("READY\n", "utf=8"))
                        await writer.drain()
                    else:
                        #counter[file_name][f'r{last_key+1}'] = [ofl, new_hash, data_is]
                        print(file_name)
                        print(revision)
                        writer.write(bytes(f"OK r{last_key}\n", "utf=8"))
                        await writer.drain()
                        writer.write(bytes("READY\n", "utf=8"))
                        await writer.drain()

                    #else:
                        #revision = last_key + 1
                        
                        # counter[file_name][1] = ofl
                        # counter[file_name][2] = new_hash
                        # counter[file_name][3] = data_is
                        # print(counter[file_name])
                        # if not os.path.exists(f"r{counter[file_name][0]}/" + file_name):
                        #     os.makedirs(f"r{counter[file_name][0]}/" + file_name)
                        #     with open(f"r{counter[file_name][0]}/" + file_name, 'wb') as f2:
                        #         f2.write(data_is)

                #print(f'{file_name}{file_length}')
                        
                        
                #print(f'{file_name}::{counter[file_name]}') 
                
                #break
            if data[0:3] == 'GET':
                get_obj = data[4:].split(' ')
                
                if len(get_obj) > 1:
                    revision = get_obj[1][1:]
                else:
                    revision = len(counter[get_obj[0][1:]].keys())
                which_file = counter[get_obj[0][1:]][f'r{revision}']
                writer.write(bytes(f"OK {which_file[0]}\n", "utf=8"))
                await writer.drain()
                writer.write(bytes(f"{which_file[2]}", "utf=8"))
                await writer.drain()
                writer.write(bytes("READY\n", "utf=8"))
                await writer.drain()
                #break
            if data[0:4] == 'LIST':
                writer.write(bytes("OK 3\n", "utf=8"))
                await writer.drain()
                writer.write(bytes("test.txt r1\n", "utf=8"))
                await writer.drain()
                writer.write(bytes("test2.txt r1\n", "utf=8"))
                await writer.drain()
                writer.write(bytes("test3.txt r1\n", "utf=8"))
                await writer.drain()
                writer.write(bytes("READY\n", "utf=8"))
                await writer.drain()

        #print("here")

async def main():
    server_state = ServerState()

    async def client_connected(reader: StreamReader, writer: StreamWriter) -> None:  # E
        client_id = uuid.uuid4()
        await server_state.add_client(reader, writer, client_id)

    server = await asyncio.start_server(client_connected, "127.0.0.1", 5003)  # F

    async with server:
        await server.serve_forever()


asyncio.run(main())
