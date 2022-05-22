import io
import sys
import re
from io import StringIO


class ProtocolEncodeException(Exception):
    def __int__(self, msg):
        super(ProtocolEncodeException, self).__int__(msg)


def init_decoder(remaining_msg):
    print(f'INIT received: {remaining_msg}')


def request_transfer_decoder(remaining_msg):
    print('TRANS received')


def next_batch_decoder(remaining_msg):
    print('NEXT received')


def finish_operation_decoder(remaining_msg):
    print('FIN received')


def continue_transmit_decoder(remaining_msg):
    print('CONT_RECEIVED')


def unknown_message_decoder(remaining_msg):
    print('Unknown message type')


MSG_DECODERS = {
    'INIT': init_decoder,
    'TRANS': request_transfer_decoder,
    'NXT': next_batch_decoder,
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

