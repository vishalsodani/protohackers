import asyncio
import logging
from asyncio import StreamReader, StreamWriter
import struct
import re

tony_address = '7YWHMfk9JZe0LM0g1ZauHuiSxhI'

class ServerState:

    async def add_client(self, reader: StreamReader, writer: StreamWriter): #A
        asyncio.create_task(self._echo(reader, writer))

    async def _echo(self, reader: StreamReader, writer: StreamWriter): #C
        try:
            host = "chat.protohackers.com"
            stream_reader, stream_writer = await asyncio.open_connection(host, 16963)
            asyncio.create_task(self._echoback(stream_reader, writer))
            while (data := await reader.readline()):
                tony = re.sub(r"(^|(?<= ))7[a-zA-Z0-9]{25,34}($|(?= ))", tony_address, data.decode("utf-8"))
                stream_writer.write(bytes(tony, "utf-8"))
                stream_writer.drain()
            stream_writer.close()

        except Exception as e:
            import traceback
            print("error ")
            traceback.print_exc()


    async def _echoback(self, reader: StreamReader, writer: StreamWriter): #C
        try:
            while (data := await reader.readline()):
                tony = re.sub(r"(^|(?<= ))7[a-zA-Z0-9]{25,34}($|(?= ))", tony_address, data.decode("utf-8"))
                writer.write(bytes(tony, "utf-8"))
                writer.drain()
            writer.close()

        except Exception as e:
            import traceback
            print("error ")
            traceback.print_exc()


async def main():
    server_state = ServerState()

    async def client_connected(reader: StreamReader, writer: StreamWriter) -> None: #E
        await server_state.add_client(reader, writer)

    server = await asyncio.start_server(client_connected, '127.0.0.1', 5003) #F

    async with server:
        await server.serve_forever()


asyncio.run(main())
