import asyncio
import logging
from asyncio import StreamReader, StreamWriter
import struct
import json
import uuid

from random import randint
from random import choice
from typing import Set
from queue import PriorityQueue

queues = {}
excluded = set()
working_q = []


def my_rand(start: int, end: int, exclude_values: Set[int] = None):
    if not exclude_values: # in this case, there are no values to exclude so there is no point in filtering out any
        return randint(start, end)
    return choice(list(set(range(start, end)).difference(exclude_values)))


class ServerState:

    def __init__(self):
        self._writers = []

    async def add_client(self, reader: StreamReader, writer: StreamWriter): #A
        self._writers.append(writer)
        asyncio.create_task(self._echo(reader, writer))

    async def _echo(self, reader: StreamReader, writer: StreamWriter): #C
        try:
            bufferobj = bytearray()
            while (data := await reader.read(1)):
                for b in data:
                    bufferobj.append(b)
                    s = bufferobj.decode('utf-8')
                    
                    if s.endswith("\n"):
                        count = s.count("\n")
                        #print(count)
                        requests = s.splitlines()
                        for r in requests:
                            #print(r)
                            j = json.loads(r)
                            if j['request'] == "get":
                                q_list =  j['queues']
                                #print(f'length of que {queues}')
                                found = False
                                priority = -1
                                res = None
                                for q in q_list:
                                    try:
                                        jobs = queues[q]
                                        #print(f'queue {q} jobs {jobs}')
                                        for job in jobs:
                                            if job['id'] not in working_q:
                                                #print(f"checking {job['pri']} against priority {priority}")
                                                if job['pri'] > priority:
                                                    res = {"status":"ok", "pri":job['pri'], "id":job["id"], "job": job["job"], "queue":q}
                                                    #print(f'response to be sent {res}')
                                                    priority = job['pri']
                                    except:
                                        import traceback
                                        traceback.print_exc()
                                if res:
                                    found = True
                                    #ltr = queues[queue_to_return]
                                    working_q.append(res['id'])
                                    #res = {"status":"ok", "pri":ltr['pri'], "id":ltr["id"], "job": ltr["job"], "queue":queue_to_return}
                                    #print(f'sending back {res}')
                                    writer.write(bytes(json.dumps(res) + "\n", "utf=8"))
                                    await writer.drain()
                                    #print("sent complete")
                                if found == False:
                                    res = {"status":"no-job"}
                                    writer.write(bytes(json.dumps(res) + "\n", "utf=8"))
                                    await writer.drain()
                                bufferobj = bytearray()
                            if j['request'] == "put":
                                unique_id = my_rand(1, 500001, excluded)
                                excluded.add(unique_id)
                                if j['queue'] not in queues:
                                    queues[j['queue']] = [{"job":j['job'], "pri": j["pri"], "id":unique_id}]
                                else:
                                    queues[j['queue']].append({"job":j['job'], "pri": j["pri"], "id":unique_id})
                                res = {"status":"ok","id":unique_id}
                                writer.write(bytes(json.dumps(res) + "\n", "utf=8"))
                                await writer.drain()
                                bufferobj = bytearray()
            #writer.close()
            #self._writers.remove(writer)

        except Exception as e:
            import traceback
            traceback.print_exc()
            logging.exception('Error reading from client.', exc_info=e)
            self._writers.remove(writer)

async def main():
    server_state = ServerState()

    async def client_connected(reader: StreamReader, writer: StreamWriter) -> None: #E
        await server_state.add_client(reader, writer)

    server = await asyncio.start_server(client_connected, '127.0.0.1', 5003) #F

    async with server:
        await server.serve_forever()


asyncio.run(main())
