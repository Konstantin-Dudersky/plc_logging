import asyncio
from asyncio.streams import StreamReader, StreamWriter
from logging import getLogger, DEBUG

log = getLogger(__name__)
log.setLevel(DEBUG)


async def handle_echo(reader: StreamReader, writer: StreamWriter):
    data = await reader.read(100)
    length = data[1]
    print("len: ", length)
    message = data[2 : length + 2].decode(encoding="utf-8")
    addr = writer.get_extra_info("peername")

    print(f"Received {message} from {addr!r}")
    writer.close()


async def main():
    server = await asyncio.start_server(handle_echo, port=4567)

    addr = [s.getsockname() for s in server.sockets]
    print(f"Serving on {addr}")

    async with server:
        await server.serve_forever()


asyncio.run(main())
