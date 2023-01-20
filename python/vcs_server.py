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

queues = {}
excluded = set()
working_q = {}
waiting_clients = []
deleted_job = []


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
        print("some")
        writer.write(bytes("READY\n", "utf=8"))
        await writer.drain()
        while data := await reader.readline():
            print(data)
            data = data.decode("utf-8").strip()
            if data == 'HELP':
                writer.write(bytes("READY\n", "utf=8"))
                await writer.drain()
            if data[0:3] == 'PUT':
                remaining_c = data[5:].split(' ')
                file_name = remaining_c[0]
                file_length = int(remaining_c[1])
                
                print(f'{file_name}{file_length}')
                try:
                    os.makedirs(os.path.dirname(file_name), exist_ok=True)
                except:
                    pass
                with open(file_name, 'wb') as f:
                        while file_length > 0:
                            content = await reader.readline()
                            f.write(content)
                            file_length -= len(content)
                        
                        
                        
                writer.write(bytes("OK r1\n", "utf=8"))
                await writer.drain()
                writer.write(bytes("READY\n", "utf=8"))
                await writer.drain()
                #break
            if data[0:3] == 'GET':
                writer.write(bytes("OK 14\n", "utf=8"))
                await writer.drain()
                writer.write(bytes("Hello, world!\n", "utf=8"))
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
