import asyncio
from asyncio import StreamReader, StreamWriter


class ServerState:

    async def add_client(self, reader: StreamReader, writer: StreamWriter): #A
        asyncio.create_task(self._echo(reader, writer))

    async def _echo(self, reader: StreamReader, writer: StreamWriter): #C
        try:
            print("reading")
            while (data := await reader.read(4)):
                print(data)
                writer.write(data)
                await writer.drain()
            writer.close()

        except Exception as e:
            import traceback
            traceback.print_exc()

async def main():
    server_state = ServerState()

    async def client_connected(reader: StreamReader, writer: StreamWriter) -> None: #E
        await server_state.add_client(reader, writer)

    server = await asyncio.start_server(client_connected, '127.0.0.1', 5003) #F

    async with server:
        await server.serve_forever()


asyncio.run(main())
