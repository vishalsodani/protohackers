from anytree import Node, RenderTree, AsciiStyle, search
import asyncio
import re
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

counter = Node("/", children=[])


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
            #print(data)
            data = data.decode("utf-8").strip()
            print(data)
            if data == 'HELP':
                writer.write(bytes("READY\n", "utf=8"))
                await writer.drain()
            if data[0:3] == 'PUT':
                remaining_c = data[5:].split(' ')
                file_name = remaining_c[0]
                #breakpoint()
                special_characters = "!\"#$%&\'()*+,:;<=>?@[\\]^_`{|}~"
                if any(c in special_characters for c in file_name) or file_name.endswith('/'):
                    print(f"rejected {file_name}")
                    writer.write(bytes(f"Err: illelgaal filename\n", "utf=8"))
                    await writer.drain()
                    break
                file_length = int(remaining_c[1])
                ofl = file_length
                data_is = ''
                revision = 1
                total = 1
                dir_name = None
                n_dir = search.find(counter, filter_=lambda node: node.name in ("/"))
                if '/' in file_name:
                    dir_name, file_name = file_name.split('/')
                    total = 2
                
                # print(file_name)
                # print([c in special_characters for c in file_name])
                # if any(c in special_characters for c in file_name):
                #     print(f"rejected {file_name}")
                #     writer.write(bytes(f"Err: illelgaal filename\n", "utf=8"))
                #     await writer.drain()
                #     continue
                # if dir_name and any(c in special_characters for c in dir_name):
                #     print(f"rejected {file_name}")
                #     writer.write(bytes(f"Err: illelgaal filename\n", "utf=8"))
                #     await writer.drain()
                #     continue
                print(f"accepted{file_name}")
                while file_length > 0:
                    content = await reader.readline()
                    data_is += content.decode("utf-8")
                    file_length -= len(content)
                if total == 2:
                    total -= 1
                    if search.find(counter, filter_=lambda node: node.name in (dir_name)) is None:
                        n_dir = Node(dir_name, parent=counter, is_dir=True)
                    else:
                        n_dir = search.find(counter, filter_=lambda node: node.name in (dir_name))
                if total == 1:
                    if search.find(counter, filter_=lambda node: node.name in (file_name)) is None:
                        #counter[file_name] = {'r1':[ofl, hashlib.md5(data_is.encode("utf-8")).hexdigest(), data_is]}
                        n = Node(file_name, parent=n_dir, is_dir=False, revisions={'r1':[ofl, hashlib.md5(data_is.encode("utf-8")).hexdigest(), data_is]})
                        #print(RenderTree(counter, style=AsciiStyle()).by_attr())
                        writer.write(bytes(f"OK r{revision}\n", "utf=8"))
                        await writer.drain()
                        writer.write(bytes("READY\n", "utf=8"))
                        await writer.drain()
                    else:
                        new_hash = hashlib.md5(data_is.encode("utf-8")).hexdigest()
                        # if counter[file_name][1] != file_length:
                        #     counter[file_name][0] += 1
                        #     counter[file_name][1] = file_length
                        
                        n = search.find(counter, filter_=lambda node: node.name in (file_name))    
                        last_key = len(n.revisions.keys())
                        if new_hash != n.revisions[f'r{last_key}'][1]:
                            n.revisions[f'r{last_key+1}'] = [ofl, new_hash, data_is]
                            revision = last_key + 1
                            writer.write(bytes(f"OK r{revision}\n", "utf=8"))
                            await writer.drain()
                            writer.write(bytes("READY\n", "utf=8"))
                            await writer.drain()
                        else:
                            #counter[file_name][f'r{last_key+1}'] = [ofl, new_hash, data_is]
                            writer.write(bytes(f"OK r{last_key}\n", "utf=8"))
                            await writer.drain()
                            writer.write(bytes("READY\n", "utf=8"))
                            await writer.drain()
            if data[0:3].upper() == 'GET':
                get_obj = data[5:].split(' ')
                get_obj_f = get_obj[0].split('/')[-1:]
                print(get_obj_f)
                n = search.find(counter, filter_=lambda node: node.name in (get_obj_f))
                if len(get_obj) > 1:
                    revision = get_obj[1][1:]
                else:
                    revision = len(n.revisions.keys())
                which_file = n.revisions[f'r{revision}']
                writer.write(bytes(f"OK {which_file[0]}\n", "utf=8"))
                await writer.drain()
                writer.write(bytes(f"{which_file[2]}", "utf=8"))
                await writer.drain()
                writer.write(bytes("READY\n", "utf=8"))
                await writer.drain()
                #break
            if data[0:4].upper() == 'LIST':
                #print(data)
                search_path = data[5:]
                if search_path == "/":
                    pass
                else:
                    search_path = search_path[1:]
                n = search.find(counter, filter_=lambda node: node.name in (search_path))
                count_ = len(n.children)
                sort_children = sorted(n.children, key=lambda x:x.name)
                #print(RenderTree(counter, style=AsciiStyle()).by_attr())
                writer.write(bytes(f"OK {count_}\n", "utf=8"))
                await writer.drain()
                
                for child in sort_children:
                    if child.is_dir == False:
                        max_rev = len(child.revisions.keys())
                        writer.write(bytes(f"{child.name} r{max_rev}\n", "utf=8"))
                        await writer.drain()
                    else:
                        writer.write(bytes(f"{child.name}/ DIR\n", "utf=8"))
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
