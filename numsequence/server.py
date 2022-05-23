import asyncio
from numsequence.protocol import ProtocolEncoder, ProtocolEncodeException
from numsequence.session import SessionHandlerFactory, SessionException
from numsequence.events import EventType
import traceback

PROTOCOL_ENCODER = ProtocolEncoder()
SESSION_HANDLER_FACTORY = SessionHandlerFactory()

SESSION_TIMEOUT = 600

async def handle_session(fut, reader, writer):
    session_handler = None
    try:
        session_processed = False
        # Change this for the FAC message
        while not session_processed:
            event = await PROTOCOL_ENCODER.decode_stream(reader)
            if session_handler is None:
                print('Here')
                session_handler = SESSION_HANDLER_FACTORY.get_session(event)

            reply = session_handler.handle_event(event)
            PROTOCOL_ENCODER.encode_message(writer, reply)
            if reply.type == EventType.FINISH_ACKNOWLEDGED:
                print('END')
                writer.close()
                session_processed = True
    except ProtocolEncodeException as pe:
        print(f'Protocol Encode Error {pe}')
    except SessionException as se:
        print(f'Protocol Encode Error {se}')
    except Exception:
        traceback.print_exc()
    print('Session done')
    fut.set_result("OK")


async def handle_connection(reader, writer):
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    task = loop.create_task(handle_session(fut, reader, writer))

    try:
        await asyncio.wait_for(fut, timeout=SESSION_TIMEOUT)
    except asyncio.TimeoutError:
        task.cancel()
        writer.close()
    except asyncio.exceptions.InvalidStateError:
        task.cancel()
        writer.close()
    finally:
        print('Session processed')


async def main():
    server = await asyncio.start_server(handle_connection, '127.0.0.1', 5000)

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
