# numsequence

A simple server and client implemented based on the [requirements](./problem-statement.md)

## Requirements

The code has been tested using `python 3.9.13` but any `python 3.X` version shall work as long as `asyncio` is 
supported.

No additional libraries needed.

## Running the code:

All commands shall be executed from the project root. Command `python` refers to a `python3.X` installation. 

### Server
`
python -m numsequence.server 5000
`

`5000` is the port number in the above example. For help type: `python -m numsequence.server`

### Client

To generate a new sequence of numbers:

`python -m numsequence.client NEW 5 5000`

or to use it with a custom client-id 

`python -m numsequence.client NEW 5 5000 --client_id 123e4567-e89b-12d3-a456-426614174000`

client-id shall be in uuid format. To continue receiving numbers after server disconnect

`python -m numsequence.client CONTINUE`

For help please type: `python -m numsequence.client NEW -h` or `python -m numsequence.client CONTINUE -h`

## The Protocol

A simple text based protocol was implemented over TCP. All messages have the same structure

`<messgae-type>,<message-content>;`

The communication has 3 main steps:

### Connection Init

Server sends an `INIT` message. The server shall reply with an `ACK`. The message has the following structure:

`INIT,<client-id>,<number-of-numbers-requested>,<batch-size>`

Batch size tells the server how many numbers it can store in one response message. 

If the `client-id` already exists and `ERR` message is returned by the server.

If any error happens during this phase communication will stop and the session timer `1 dec` on server
side will tear-down the connection.

Another way to init a connection is to continue the receiving numbers after connection is lost.

Server sends a `CONT` message and server responds with an `ACK`. The message has the following structure:

`CONT,<client-id>`

If the requested `client-id` does not exist an `ERR` message is returned by the server. 

### Transfer of numbers:

The client sends a `RECV` message and the server returns a `NUM` message.

For example:
```commandline
Sending message: RECV,0;
Received: NUM,6:41:81:68:68;
```
The client requested index 0 of the bathes of numbers. For example the user request 10 numbers and the batch size is 
5 the server can deliver the numbers 5 by 5.

The server responds with numbers generated. The numbers are separated by `:`

The client can request any batch index as long as the index is valid.

### Saying Goodbye

The client can indicate that no more batch is expected by sending a `FIN` message. The server responds with a `FAC` 
message, which contains the checksum.

Example:
```commandline
Sending message: 'FIN;'
Received: FAC,f90b20dae8c9b7d7be2a5fb7cc856e8b;
```

After this message the client closes the connection, calculates the sum of the numbers and validates the checksum.

The checksum is an `md5` hash of the string representation of a python list containing all the numbers generated
by the server in the correct order.

## Testing

Due to the short timeframe no automated unit or integration test have been implemented. Manual testing was 
introduced.

Before testing the following environment variable shall be set for the server.

```commandline
export TEST_MODE=1
```

If this variable is set the server will use the client-id to initialise the PRNG used to generate number this way
the following examples shall work for the user.

### Test 1 - Check the generation of a new sequence

`python -m numsequence.client NEW 5 5000 --client_id 123e4567-e89b-12d3-a456-426614174000`

The client shall show the following response:

```commandline
Sending message: 'INIT,123e4567-e89b-12d3-a456-426614174000,5,5;'
Received: ACK;
Requesting numbers
Sending message: 'RECV,0;'
Received: NUM,6:41:81:68:68;
Sending message: 'FIN;'
Received: FAC,f90b20dae8c9b7d7be2a5fb7cc856e8b;
Closing the connection
The SUM of numbers is: 264
Checksum (f90b20dae8c9b7d7be2a5fb7cc856e8b) is valid!
```
### Test 2 - Check the generation of a new sequence within 30 seconds 

`python -m numsequence.client NEW 5 5000 --client_id 123e4567-e89b-12d3-a456-426614174000`

and within 30 seconds execute the same command

`python -m numsequence.client NEW 5 5000 --client_id 123e4567-e89b-12d3-a456-426614174000`

The expected result is:

```commandline
Sending message: 'INIT,123e4567-e89b-12d3-a456-426614174000,5,5;'
Received: ERR,123e4567-e89b-12d3-a456-426614174000 already exist;
```

### Test 3 - Check that client can continue in case of server disconnect

Set a big number for the required messages. Like `10000`. Because of verbose logging to the console most likely
not all numbers can be processed within the `1s` session timeout on server side. (If you have a stronger machine
you may have to request even more numbers - MAx is 0xffff)

`python -m numsequence.client NEW 10000 5000 --client_id 123e4567-e89b-12d3-a456-426614174000`

You shall see something like:

```
...
Sending message: 'RECV,630;'
Received: NUM,54:94:94:19:96;
Sending message: 'RECV,631;'
ERROR: [Errno 54] Connection reset by peer
```

Then run the following command:

`python -m numsequence.client CONTINUE 5000`

If the connection drops again, repeat the following command until you receive:

```commandline
Received: NUM,40:53:59:98:3;
Sending message: 'FIN;'
Received: FAC,589f9ca74cb5ea9a32eddd14840d5b64;
Closing the connection
The SUM of numbers is: 504721
Checksum (589f9ca74cb5ea9a32eddd14840d5b64) is valid!
```


### Test 4 - Test that continue can be executed after init and sum is recalculated properly

Execute the following command:

`python -m numsequence.client NEW 10 5000 --client_id 123e4567-e89b-12d3-a456-426614174000`

You shall receive:

```commandline
Sending message: 'INIT,123e4567-e89b-12d3-a456-426614174000,10,5;'
Received: ACK;
Requesting numbers
Sending message: 'RECV,0;'
Received: NUM,6:41:81:68:68;
Sending message: 'RECV,1;'
Received: NUM,41:10:40:78:98;
Sending message: 'FIN;'
Received: FAC,9b14501c5359fb4eac96df9e874348b2;
Closing the connection
The SUM of numbers is: 531
Checksum (9b14501c5359fb4eac96df9e874348b2) is valid!
```

now execute the following command immediately

`python -m numsequence.client CONTINUE 5000`

You shall see the following:

```commandline
Sending message: 'CONT,123e4567-e89b-12d3-a456-426614174000;'
Received: ACK;
Requesting numbers
Skipping chunk-nr: 0
Skipping chunk-nr: 1
Sending message: 'FIN;'
Received: FAC,9b14501c5359fb4eac96df9e874348b2;
Closing the connection
The SUM of numbers is: 531
Checksum (9b14501c5359fb4eac96df9e874348b2) is valid!
```

As long as client-data is not purged the sum of the numbers shall be available. (Even if TEST_DEV is not set for
the server the sum shall remain the same between the first and second execution of the client)

### Test 5 - Test that client-data is purged after 30 seconds

Execute:

`python -m numsequence.client NEW 10 5000 --client_id 123e4567-e89b-12d3-a456-426614174000`

Shall return:

```commandline
Sending message: 'INIT,123e4567-e89b-12d3-a456-426614174000,10,5;'
Received: ACK;
Requesting numbers
Sending message: 'RECV,0;'
Received: NUM,6:41:81:68:68;
Sending message: 'RECV,1;'
Received: NUM,41:10:40:78:98;
Sending message: 'FIN;'
Received: FAC,9b14501c5359fb4eac96df9e874348b2;
Closing the connection
The SUM of numbers is: 531
Checksum (9b14501c5359fb4eac96df9e874348b2) is valid!
```

Make sure you wait `30 seconds`. In the terminal window of the server you shall see 

`Purging client info for: 123e4567-e89b-12d3-a456-426614174000`

Now execute the following:

`python -m numsequence.client CONTINUE 5000`

The client terminal shall show:

```commandline
Sending message: 'CONT,123e4567-e89b-12d3-a456-426614174000;'
Received: ERR,Client-id: 123e4567-e89b-12d3-a456-426614174000 does not exist;
```