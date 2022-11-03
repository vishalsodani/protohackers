import asyncio
import logging
from asyncio import StreamReader, StreamWriter
import struct

message_length = 9

class ServerState:

    def __init__(self):
        self._writers = []

    async def add_client(self, reader: StreamReader, writer: StreamWriter): #A
        self._writers.append(writer)
        asyncio.create_task(self._echo(reader, writer))

    async def _echo(self, reader: StreamReader, writer: StreamWriter): #C
        try:
            prices = []
            bufferobj = bytearray()
            start_index = 0
            while (data := await reader.read(4)):
                for b in data:
                    bufferobj.append(b)
                    if len(bufferobj) % message_length == 0:
                        (instruction, timestamp, price) = struct.unpack(
                        "!cii", bufferobj[start_index : start_index + message_length]
                        )
                        instruction = instruction.decode('utf-8')
                        if instruction == "Q":
                            filterd = sorted(prices, key=lambda s: s[1][0])
                            eligible_prices = [
                                i
                                for i in filterd
                                if i[1][0] >= timestamp and i[1][0] <= price
                            ]
                            tot = 0
                            for p in eligible_prices:
                                tot += p[1][1]
                            if len(eligible_prices) == 0:
                                res = 0
                            else:
                                res = tot // len(eligible_prices)
                            start_index += message_length
                            writer.write(struct.pack("!i", res))
                            writer.drain()
                        if instruction == "I":
                            prices.append([instruction, (timestamp, price)])
                            start_index += message_length
            writer.close()
            self._writers.remove(writer)

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
