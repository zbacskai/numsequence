import asyncio
from numsequence.protocol import ProtocolEncoder, ProtocolEncodeException
from numsequence.session import SessionHandlerFactory, SessionException
from numsequence.events import EventType
import traceback
import uuid

PROTOCOL_ENCODER = ProtocolEncoder()
SESSION_HANDLER_FACTORY = SessionHandlerFactory()

SESSION_TIMEOUT = 1

async def handle_session(fut, reader, writer):
    try:
        session_processed = False
        session_handler = None
        while not session_processed:
            event = await PROTOCOL_ENCODER.decode_stream(reader)
            session_handler = SESSION_HANDLER_FACTORY.get_session(event) if session_handler is None else session_handler
            reply = session_handler.handle_event(event)
            PROTOCOL_ENCODER.encode_message(writer, reply)
            session_processed = (reply.type == EventType.FINISH_ACKNOWLEDGED)
    except ProtocolEncodeException as pe:
        print(f'Protocol Encode Error {pe}')
        traceback.print_exc()
    except SessionException as se:
        print(f'Session exception {se}')
        traceback.print_exc()
    except Exception:
        traceback.print_exc()
    finally:
        writer.close()
        fut.set_result("OK")


def handle_session_execution_exception(task, writer, message):
    task.cancel()
    writer.close()
    print(message)

async def handle_connection(reader, writer):
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    task = loop.create_task(handle_session(fut, reader, writer))

    session_id = uuid.uuid4()
    print(f'Session {session_id} has started')
    try:
        await asyncio.wait_for(fut, timeout=SESSION_TIMEOUT)
    except asyncio.TimeoutError:
        handle_session_execution_exception(task, writer, f'Session {session_id} has finished (timeout')
    except asyncio.exceptions.InvalidStateError:
        handle_session_execution_exception(task, writer, f'Session {session_id} has finished (connection invalid state')
    else:
        print(f'Session {session_id} has finished')


async def main():
    server = await asyncio.start_server(handle_connection, '127.0.0.1', 5000)

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
