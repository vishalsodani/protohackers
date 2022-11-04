import asyncio
import logging
from asyncio import StreamReader, StreamWriter
import struct
import re

tony_address = '7YWHMfk9JZe0LM0g1ZauHuiSxhI'

class ServerState:

    async def add_client(self, reader: StreamReader, writer: StreamWriter):
        asyncio.create_task(self._client(reader, writer))

    async def _client(self, reader: StreamReader, writer: StreamWriter):
        try:
            host = "chat.protohackers.com"
            stream_reader, stream_writer = await asyncio.open_connection(host, 16963)
            asyncio.create_task(self._upstream(stream_reader, writer))
            while (data := await reader.readline()):
                tony = re.sub(r"(^|(?<= ))7[a-zA-Z0-9]{25,34}($|(?= ))", tony_address, data.decode("utf-8"))
                stream_writer.write(bytes(tony, "utf-8"))
                await stream_writer.drain()
            stream_writer.close()

        except Exception as e:
            import traceback
            print("error ")
            traceback.print_exc()


    async def _upstream(self, reader: StreamReader, writer: StreamWriter):
        try:
            while (data := await reader.readline()):
                tony = re.sub(r"(^|(?<= ))7[a-zA-Z0-9]{25,34}($|(?= ))", tony_address, data.decode("utf-8"))
                writer.write(bytes(tony, "utf-8"))
                await writer.drain()
            writer.close()

        except Exception as e:
            import traceback
            print("error ")
            traceback.print_exc()


async def main():
    server_state = ServerState()

    async def client_connected(reader: StreamReader, writer: StreamWriter) -> None:
        await server_state.add_client(reader, writer)

    server = await asyncio.start_server(client_connected, '127.0.0.1', 5003)

    async with server:
        await server.serve_forever()


asyncio.run(main())
