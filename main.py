import asyncio
from asyncio.streams import StreamReader, StreamWriter
from logging import getLogger, DEBUG

log = getLogger(__name__)
log.setLevel(DEBUG)


async def handle_echo(reader: StreamReader, writer: StreamWriter):
    data = await reader.read(100)
    # message = data.decode(encoding="ascii")
    addr = writer.get_extra_info("peername")

    print(f"Received {data!r} from {addr!r}")
    writer.close()


async def main():
    server = await asyncio.start_server(handle_echo, port=4567)

    addr = server.sockets[0].getsockname()
    print(f"Serving on {addr}")

    async with server:
        await server.serve_forever()


asyncio.run(main())
