import io
import sys
import re
from io import StringIO
from numsequence.events import InitEvent, ReceiveEvent, FinishEvent, ContinueEvent, EventType


class ProtocolEncodeException(Exception):
    def __int__(self, msg):
        super(ProtocolEncodeException, self).__int__(msg)


def init_decoder(remaining_msg):
    print(f'INIT received: {remaining_msg}')
    msg_info = re.search(r'([0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}),([0-9]+),([0-9]+)', remaining_msg)
    if msg_info is None:
        raise ProtocolEncodeException(f'Failed to decode {remaining_msg}')

    client_id, number_of_numbers, batch_size = msg_info.group(1, 2, 3)
    return InitEvent(client_id, int(number_of_numbers), int(batch_size))


def request_transfer_decoder(remaining_msg):
    print(f'RECV received {remaining_msg}')
    msg_info = re.search(r'([0-9]+)', remaining_msg)
    if msg_info is None:
        raise ProtocolEncodeException(f'Failed to decode {remaining_msg}')

    next_message_index = msg_info.group(1)
    return ReceiveEvent(int(next_message_index))


def finish_operation_decoder(remaining_msg):
    print(f'FIN received {remaining_msg}')
    return FinishEvent()


def continue_transmit_decoder(remaining_msg):
    print(f'CONT_RECEIVED {remaining_msg}')
    msg_info = re.search(
        r'([0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12})',
        remaining_msg)
    if msg_info is None:
        raise ProtocolEncodeException(f'Failed to decode {remaining_msg}')

    client_id = msg_info.group(1)
    return ContinueEvent(client_id)


def unknown_message_decoder(remaining_msg):
    print(f'Unknown message type {remaining_msg}')
    return None


MSG_DECODERS = {
    'INIT': init_decoder,
    'RECV': request_transfer_decoder,
    'FIN': finish_operation_decoder,
    'CONT': continue_transmit_decoder,
}

MAX_MSG_PREAMBLE = max([len(x) for x in MSG_DECODERS.keys()]) + 1 + len(f'{sys.maxsize}') + 1


async def read_buffer(full_message, reader):
    msg_part = await reader.read(1)
    full_message.seek(0, io.SEEK_END)
    full_message.write(msg_part.decode())
    full_message.seek(0)


class ProtocolEncoder():
    def _decode_message(self, message):
        msg_info = re.search(r'([A-Z]+)[,;](.*)', message)
        if msg_info is None:
            raise ProtocolEncodeException(f'Failed to decode {message}')

        return MSG_DECODERS.get(msg_info.group(1), unknown_message_decoder)(msg_info.group(2))

    async def decode_stream(self, reader):
        full_message = StringIO('')
        while re.search(r'([-A-Za-z0-9,]+);(.*)', full_message.read()) is None:
            await read_buffer(full_message, reader)

        full_message.seek(0)
        return self._decode_message(full_message.read())

    def encode_message(self, writer, event):
        if event.type == EventType.ACKNOWLEDGE:
            writer.write('ACK;'.encode())
        if event.type == EventType.NUMBERS:
            numlist = ':'.join([str(e) for e in event.numbers])
            writer.write(f'NUM,{numlist};'.encode())
        if event.type == EventType.FINISH_ACKNOWLEDGED:
            writer.write(f'FAC,{event.checksum};'.encode())