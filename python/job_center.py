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
working_q = {}
waiting_clients = []


def my_rand(start: int, end: int, exclude_values: Set[int] = None):
    if not exclude_values: # in this case, there are no values to exclude so there is no point in filtering out any
        return randint(start, end)
    return choice(list(set(range(start, end)).difference(exclude_values)))


class ServerState:

    def __init__(self):
        self._writers = []

    async def add_client(self, reader: StreamReader, writer: StreamWriter, client_id): #A
        self._writers.append([writer, client_id])
        asyncio.create_task(self._echo(reader, writer, client_id))

    async def _echo(self, reader: StreamReader, writer: StreamWriter, client_id): #C
        try:
            global working_q
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
                                    working_q[res['id']] = client_id
                                    #res = {"status":"ok", "pri":ltr['pri'], "id":ltr["id"], "job": ltr["job"], "queue":queue_to_return}
                                    print(f'sending back {res}')
                                    writer.write(bytes(json.dumps(res) + "\n", "utf=8"))
                                    await writer.drain()
                                    #print("sent complete")
                                if found == False:
                                    if 'wait' in j and j['wait'] == True:
                                        waiting_clients.append([client_id, j['queues'], writer])
                                    else:
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
                            if j["request"] == "abort":
                                job_id_is = j["id"]
                                if client_id == working_q[job_id_is]:
                                    res = {"status":"ok"}
                                    writer.write(bytes(json.dumps(res) + "\n", "utf=8"))
                                    await writer.drain()
                                    del working_q[job_id_is]
                                # else:
                                #     res = {"status":"ok"}
                                #     writer.write(bytes(json.dumps(res) + "\n", "utf=8"))
                                #     await writer.drain()
                                bufferobj = bytearray()
                            if j["request"] == "delete":
                                job_id_is = j["id"]
                                for q_u in queues:
                                    working_on = queues[q_u]
                                    for job in working_on.copy():
                                        if job_id_is == job['id']:
                                            working_on.remove(job)
                                            res = {"status":"ok"}
                                            writer.write(bytes(json.dumps(res) + "\n", "utf=8"))
                                            await writer.drain()


                                bufferobj = bytearray()
            
            writer.close()
            #working_q = {}
            #global working_q
            for k, v in working_q.copy().items():
                if v == client_id:
                    #print(f"delete for {client_id}")
                    del working_q[k]
                    if len(waiting_clients) > 0:
                        waiting_list = waiting_clients[0][1]
                        write_to_client = waiting_clients[0][2]
                        
                        for w in waiting_list:
                            jobs = queues[w]
                            for job in jobs:
                                if job['id'] not in working_q:
                                    res = {"status":"ok", "pri":job['pri'], "id":job["id"], "job": job["job"], "queue":w}
                                    write_to_client.write(bytes(json.dumps(res) + "\n", "utf=8"))
                                    await write_to_client.drain()
                                    working_q[job['id']] = waiting_clients[0][0]
  

            
            #self._writers.remove(writer)
        except ConnectionError:
            print("error")
            
            #working_q = {}
        except Exception as e:
            import traceback
            traceback.print_exc()
            logging.exception('Error reading from client.', exc_info=e)
            #working_q = {}
            #self._writers.remove(writer)

async def main():
    server_state = ServerState()

    async def client_connected(reader: StreamReader, writer: StreamWriter) -> None: #E
        client_id = uuid.uuid4()
        await server_state.add_client(reader, writer, client_id)

    server = await asyncio.start_server(client_connected, '127.0.0.1', 5003) #F

    async with server:
        await server.serve_forever()


asyncio.run(main())
