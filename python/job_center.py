import asyncio
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

queues = {}
excluded = set()
working_q = {}
waiting_clients = []
deleted_job = []

def my_rand(start: int, end: int, exclude_values: Set[int] = None):
    if not exclude_values: # in this case, there are no values to exclude so there is no point in filtering out any
        return randint(start, end)
    return choice(list(set(range(start, end)).difference(exclude_values)))

async def send_response(writer, res):
    writer.write(bytes(json.dumps(res) + "\n", "utf=8"))
    await writer.drain()

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
            while (data := await reader.readline()):
                for b in data:
                    bufferobj.append(b)
                    s = bufferobj.decode('utf-8')
                # print("----SSSSSSSS")
                # print(s)
                # print("--end--SSSSSSSS")
                if s.endswith("\n"):
                        bufferobj = bytearray()
                        print(f"before splitting {s}")
                        count = s.count("\n")
                        #print(count)
                        requests = s.splitlines()
                        #print(f"total requests {requests} at {datetime.now()} and count {count > 1}")
                        for r in requests:
                            good = True
                            #print(f"request from {client_id}: {r}")
                            try:
                                j = json.loads(r)
                                if 'request' not in j:
                                    #print(client_id)
                                    good = False
                                    res = {"status":"error","error":"Unrecognised request type."}
                                    await send_response(writer, res)
                                    break
                            except:
                                #print(client_id)
                                good = False
                                res = {"status":"error","error":"Unrecognised request type."}
                                await send_response(writer, res)
                                break
                            if good and j['request'] == "get":
                                q_list =  j['queues']
                                found = False
                                priority = -1
                                res = None
                                for q in q_list:
                                    try:
                                        jobs = queues[q]
                                        not_in_q = filter(lambda x:x['id'] not in working_q, jobs)
                                        highest = heapq.nlargest(1, not_in_q, lambda x:x['pri'])
                                        if len(highest) > 0 and highest[0]['pri'] > priority:
                                            res = {"status":"ok", "pri":highest[0]['pri'], "id":highest[0]["id"], "job": highest[0]["job"], "queue":q}
                                            priority = highest[0]['pri']
                                    except:
                                        import traceback
                                        traceback.print_exc()
                                if res:
                                    found = True
                                    #ltr = queues[queue_to_return]
                                    working_q[res['id']] = client_id
                                    #print(f"job id in working q added {res['id']}")
                                    #res = {"status":"ok", "pri":ltr['pri'], "id":ltr["id"], "job": ltr["job"], "queue":queue_to_return}
                                    #print(f'sending back {res}')
                                    await send_response(writer, res)
                                    #print(f"response of get at {datetime.now()}")
                                    #print("sent complete")
                                if found == False:
                                    if 'wait' in j and j['wait'] == True:
                                        waiting_clients.append([client_id, j['queues'], writer])
                                    else:
                                        #print(r)
                                        res = {"status":"no-job"}
                                        await send_response(writer, res)
                                bufferobj = bytearray()
                            if good and j['request'] == "put":
                                unique_id = my_rand(1, 500001, excluded)
                                excluded.add(unique_id)
                                print(f"job id created {unique_id}")
                                if j['queue'] not in queues:
                                    queues[j['queue']] = [{"job":j['job'], "pri": j["pri"], "id":unique_id}]
                                else:
                                    queues[j['queue']].append({"job":j['job'], "pri": j["pri"], "id":unique_id})
                                res = {"status":"ok","id":unique_id}
                                await send_response(writer, res)
                                bufferobj = bytearray()
                            if good and j["request"] == "abort":
                                job_id_is = j["id"]
                                #print(client_id)
                                if job_id_is in deleted_job or job_id_is not in working_q:
                                    # print('abort start')
                                    # print(working_q)
                                    # # print(job_id_is in deleted_job)
                                    # # print(job_id_is not in working_q)
                                    # # print(r)
                                    # print('abort end')
                                    res = {"status":"no-job"}
                                    await send_response(writer, res)
                                    print(f"response of abort at {datetime.now()}")
                                    break
                                    
                                if job_id_is not in deleted_job and job_id_is in working_q and client_id == working_q[job_id_is] :
                                    del working_q[job_id_is]
                                    res = {"status":"ok"}
                                    await send_response(writer, res)
                                    print(f"response of abort at {datetime.now()}")
                                if job_id_is in working_q and client_id != working_q[job_id_is]:
                                    print(f"job is in working q but for diff erent client {working_q[job_id_is]} so cannot abort {job_id_is}")
                                    res = {"status":"error","error":"Unrecognised request type."}
                                    await send_response(writer, res)
                                    print(f"response of abort at {datetime.now()}")
                                
                                    
                                # if job_id_is not in deleted_job and job_id_is in working_q:
                                #     res = {"status":"ok"}
                                #     await send_response(writer, res)
                                    #break
                                # else:
                                #     res = {"status":"ok"}
                                #     writer.write(bytes(json.dumps(res) + "\n", "utf=8"))
                                #     await writer.drain()
                                bufferobj = bytearray()
                            if good and j["request"] == "delete":
                                #print(f"delete request {j}")
                                job_id_is = j["id"]
                                for q_u in queues:
                                    working_on = queues[q_u]
                                    for job in working_on.copy():
                                        if job_id_is in deleted_job:
                                            #print(r)
                                            res = {"status":"no-job"}
                                            await send_response(writer, res)
                                            break
                                        if job_id_is == job['id']:
                                            deleted_job.append(job['id'])
                                            #print(f'deleted job q is {deleted_job} added {job["id"]}')
                                            #print(f'working q {working_q} before delete {job_id_is}')
                                            working_on.remove(job)
                                            #print(f'working q {working_q} after delete {job_id_is}')
                                            if job_id_is in working_q:
                                                print(f"job id deleted from working q {job_id_is}")
                                                del working_q[job_id_is]
                                            print(f"job id in added to delete queue {job_id_is}")
                                            res = {"status":"ok"}
                                            await send_response(writer, res)
                                            break


                                bufferobj = bytearray()
            
            #writer.close()
            #working_q = {}
            #global working_q
            #print(client_id)
            for k, v in working_q.copy().items():
                if v == client_id:
                    #print(f"delete for {client_id}")
                    del working_q[k]
                    if len(waiting_clients) > 0:
                        #print(f'waiting clients are {len(waiting_clients)}')
                        #waiting_list = waiting_clients[0][1]
                        #write_to_client = waiting_clients[0][2]
                        
                        for waits in waiting_clients.copy():
                            write_to_client = waits[2]
                            priority = -1
                            res = None
                            for w in waits[1]:
                                jobs = queues[w]
                                not_in_q = filter(lambda x:x['id'] not in working_q, jobs)
                                highest = heapq.nlargest(1, not_in_q, lambda x:x['pri'])
                                if len(highest) > 0 and highest[0]['pri'] > priority:
                                    res = {"status":"ok", "pri":highest[0]['pri'], "id":highest[0]["id"], "job": highest[0]["job"], "queue":q}
                                    priority = highest[0]['pri']
                                    print(f"waiting queue passed job {q}")
                                    # if job['id'] not in working_q:
                                    #     if job['pri'] > priority:
                                    #         res = {"status":"ok", "pri":job['pri'], "id":job["id"], "job": job["job"], "queue":q}
                                    #         priority = job['pri']
                                if res:
                                    write_to_client.write(bytes(json.dumps(res) + "\n", "utf=8"))
                                    await write_to_client.drain()
                                    working_q[highest[0]['id']] = waits[0]
                                    waiting_clients.remove(waits)
            #writer.close()
    

            
            #self._writers.remove(writer)
        except ConnectionError:
            print("error")
            import traceback
            traceback.print_exc()
            #working_q = {}
        except Exception as e:
            
            
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
