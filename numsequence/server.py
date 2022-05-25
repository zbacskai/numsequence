import asyncio
from numsequence.protocol import ProtocolEncoder, ProtocolEncodeException
from numsequence.session import SessionHandlerFactory, SessionException
from numsequence.session_storage import SessionStorage
from numsequence.events import EventType
import traceback
import uuid
import argparse

SESSION_TIMEOUT = 1


async def handle_session(fut, reader, writer, server):
    try:
        session_processed = False
        session_handler = None
        while not session_processed:
            event = await server.protocol_encoder.decode_stream(reader)
            session_handler = server.session_handler_factory.get_session_handler(
                event) if session_handler is None else session_handler
            reply = session_handler.handle_event(event)
            server.protocol_encoder.encode_message(writer, reply)
            session_processed = (reply.type == EventType.FINISH_ACKNOWLEDGED)
    except ProtocolEncodeException as pe:
        print(f'Protocol Encode Error {pe}')
    except SessionException as se:
        print(f'Session exception {se}')
    except ConnectionResetError as ce:
        print(f'Connection exception {ce}')
    except Exception as ex:
        print(f'Exception: {ex}')
        traceback.print_exc()
    else:
        fut.set_result("OK")
    finally:
        writer.close()


def handle_session_execution_exception(task, writer, message):
    task.cancel()
    writer.close()
    print(f"Session execution problem {message}")


class Server:
    def __init__(self):
        self.session_handler_factory = SessionHandlerFactory(SessionStorage())
        self.protocol_encoder = ProtocolEncoder()

    async def handle_connection(self, reader, writer):
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        task = loop.create_task(handle_session(fut, reader, writer, self))

        session_id = uuid.uuid4()
        print(f'Session {session_id} has started')
        try:
            await asyncio.wait_for(fut, timeout=SESSION_TIMEOUT)
        except asyncio.TimeoutError:
            handle_session_execution_exception(task, writer, f'Session {session_id} has finished (timeout')
        except asyncio.exceptions.InvalidStateError:
            handle_session_execution_exception(task, writer,
                                               f'Session {session_id} has finished (connection invalid state')
        else:
            print(f'Session {session_id} has finished')


async def main(arguments):
    server = Server()
    server = await asyncio.start_server(server.handle_connection, '127.0.0.1', arguments.port)

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help='The port to listen on localhost', type=int)
    arguments = parser.parse_args()
    asyncio.run(main(arguments))
