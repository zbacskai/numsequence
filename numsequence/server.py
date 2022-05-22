import asyncio
from numsequence.protocol import ProtocolEncoder, ProtocolEncodeException

PROTOCOL_ENCODER = ProtocolEncoder()

async def handle_session(fut, reader, writer):
    try:
        await PROTOCOL_ENCODER.decode_stream(reader)
    except ProtocolEncodeException as pe:
        print(f'Protocol Encode Error {pe}')
    fut.set_result("OK")


async def handle_connection(reader, writer):
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    task = loop.create_task(handle_session(fut, reader, writer))

    try:
        await asyncio.wait_for(fut, timeout=10)
    except asyncio.TimeoutError:
        task.cancel()
    except asyncio.exceptions.InvalidStateError:
        task.cancel()
    finally:
        writer.close()


async def main():
    server = await asyncio.start_server(handle_connection, '127.0.0.1', 5000)

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
