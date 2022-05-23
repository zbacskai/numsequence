import asyncio
import uuid

async def tcp_echo_client():
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', 5000)

    client_id = uuid.uuid4()
    message = f'INIT,{client_id},22,5;'
    print(f'Send: {message!r}')
    writer.write(message.encode())
    await writer.drain()

    data = await reader.read(1024)
    response = data.decode()
    print(f'Received: {response}')

    if response == 'ACK;':
        for i in range(0, 5):
            print('Requesting messages')
            writer.write(f'RECV,{i};'.encode())
            await writer.drain()
            data = await reader.read(1024)
            response = data.decode()
            print(f'Received: {response}')

    writer.write(f'FIN;'.encode())
    await writer.drain()
    data = await reader.read(1024)
    response = data.decode()
    print(f'Received: {response}')

    print('Close the connection')
    writer.close()
    await writer.wait_closed()

if __name__ == '__main__':
    asyncio.run(tcp_echo_client())