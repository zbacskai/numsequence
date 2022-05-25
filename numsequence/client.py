import asyncio
import uuid
import argparse
import shelve
import re
import math
import hashlib

BATCH_SIZE = 5.0

async def send_message(writer, message):
    print(f'Sending message: {message!r}')
    writer.write(message.encode())
    await writer.drain()

async def read_message(reader):
    data = await reader.read(1024)
    response = data.decode()
    print(f'Received: {response}')
    return response

def get_client_id(shelve_obj, is_continue):
    if is_continue and 'client-id' in shelve_obj:
        return shelve_obj['client-id']

    return uuid.uuid4()

async def init_dialogue(writer, reader, client_id, arguments, client_state):
    if arguments.command == 'NEW':
        await send_message(writer, f'INIT,{client_id},{arguments.number_of_numbers},{BATCH_SIZE};')
        client_state['client-id'] = client_id
        client_state['number-of-messages'] = arguments.number_of_numbers
        client_state['batch-size'] = BATCH_SIZE
        client_state['numbers'] = {}
        client_state['checksum'] = ''
    else:
        await send_message(writer, f'CONT,{client_id};')

    # Wait for ACK
    ack_msg = await read_message(reader)
    return ack_msg == 'ACK;'

def decode_checksum(message):
    msg_info = re.search(r'FAC,([A-Za-z0-9]+);().*', message)
    if msg_info is None:
        raise Exception(f'Failed to decode {message}')

    return msg_info.group(1)

async def finish_dialogue(reader, writer):
    await send_message(writer, 'FIN;')
    fac_message = await read_message(reader)

    checksum = decode_checksum(fac_message)
    print('Closing the connection')
    writer.close()
    await writer.wait_closed()
    return checksum

def decode_numbers(numbers_msg, client_state_numbers, index):
    msg_info = re.search(r'NUM,([0-9:]+);().*', numbers_msg)
    if msg_info is None:
        raise Exception(f'Failed to decode {numbers_msg}')

    client_state_numbers.setdefault(index, [int(x) for x in msg_info.group(1).split(':')])

async def read_all_numbers(reader, writer, client_state):
    number_of_messages = int(math.ceil(float(client_state['number-of-messages'])/float(client_state['batch-size'])))
    print('Requesting numbers')
    client_state_numbers = client_state['numbers']
    for i in range(0, number_of_messages):
        if i not in client_state['numbers']:
            await send_message(writer, f'RECV,{i};')
            numbers_msg = await read_message(reader)
            decode_numbers(numbers_msg, client_state_numbers, i)

    client_state['numbers'] = client_state_numbers

def calculate_and_validate_result(client_state):
    all_nums = []
    for _, batch_of_numbers in client_state['numbers'].items():
        all_nums.extend(batch_of_numbers)
    print(f'The SUM of numbers is: {sum(all_nums)}')
    chksum = hashlib.md5(f'{all_nums}'.encode())
    chksum = chksum.hexdigest()
    if chksum == client_state['checksum']:
        print(f'Checksum ({chksum}) is valid!')
    else:
        print(f'Checksum calculated({chksum}) does not match received ({client_state["checksum"]})')

async def numsequence_client(fut, arguments):
    is_continue = arguments.command == 'CONTINUE'
    try:
        with shelve.open('.client_state') as client_state:
            reader, writer = await asyncio.open_connection(
                '127.0.0.1', arguments.port)

            client_id = get_client_id(client_state, is_continue)
            if await init_dialogue(writer, reader, client_id, arguments, client_state):
                await read_all_numbers(reader, writer, client_state)
                client_state['checksum'] = await finish_dialogue(reader, writer)
                calculate_and_validate_result(client_state)
    except Exception as e:
        print(f'Exception {e}')
    finally:
        fut.set_result(0)

async def numsequence_client_worker(arguments):
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    task = loop.create_task(numsequence_client(fut, arguments))

    try:
        await asyncio.wait_for(fut, timeout=3)
    except asyncio.TimeoutError:
        print("Server error, failed to receive results within timeframe.")
        task.cancel()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='Command to run - NEW or CONTINUE', dest='command')

    new_parser = subparsers.add_parser('NEW')
    continue_parser = subparsers.add_parser('CONTINUE')

    new_parser.add_argument("number_of_numbers", help='The amount of numbers to be requested from server', type=int)
    new_parser.add_argument("port", help='The port to connect to on localhost', type=int)

    continue_parser.add_argument("port", help='The port to connect to on localhost', type=int)

    arguments = parser.parse_args()
    if arguments.command is None:
        parser.print_help()
    else:
        asyncio.run(numsequence_client_worker(arguments))
