## Overview

The problem is to implement a client and server that implement a protocol of your own design that meets the requirements given below.

The high-level requirement is that a client establishes a stateful connection to the server and receives a stream of messages whose primary payload is a number; the sequence of messages delivered to the client conforms to the description below. The aim of the protocol is to ensure that the client/server dialogue is correctly achieved, even when the client connection can be dropped from time to time.

### Client & server description

The client's job is to connect to the server and receive a complete sequence of `n` numbers, close the connection, and return the sum of the received numbers. It can be started with an optional argument that specifies the number `n` of messages to receive (up to a maximum of `0xffff`), or else chooses randomly from that range. The client also generates a random uuid client identifier string. Both are sent to the server these as part of the connection request.

On receiving a connection request the server randomly initialises a PRNG which generates a sequence of uint32 numbers and sends this sequence in a stream of discrete messages, 1s apart. The final message also contains a checksum that may be used by the client to verify that it has correctly received the entire sequence. The server closes the connection after sending the final message.

The client's job is to receive the sequence and, once all messages have been received, close the connection, calculate the checksum, and compare with the value supplied by the server. The client must be capable of reconnecting and continuing to receive the sequence in the case that its connection drops; when reconnecting, the client must supply connection parameters that allow the server to continue the sequence starting with the first undelivered number. The final checksum(s), and an indication of success or failure, is output to stdout.

The complete sequence of numbers delivered by the server must be the same irrespective of disconnections by the client. The server must maintain session state for each client (ie state for each client id) in order to implement this functionality.

The server must maintain session state for up to 30s during periods of disconnection. If a client fails to reconnect within 30s of a disconnection then the server discards the state, and any subsequent reconnection attempt for that client id must be rejected with a suitable error. The session state for a given client id must be discarded after the sequence has completed.

An abstraction must be defined representing the interface betweem the server and a session state store, and an implementation of an in-memory store (ie for use by a single server instance) must be provided. However, the interface must be capable of implementation as a shared session store (eg using Redis) which could be shared by multiple server instances (so reconnections can succeed if made to a different server from the original connection).

## Server requirements

The server must listen on the localhost interface using a port specified as a commandline argument.

The server must be capable of handling multiple clients concurrently.

## Client requirements

The client must connect to the server via the port specified as a commandline argument. The result (ie the sum/checksum of the received numbers) must be written to  stdout.

## Test requirements

Some test mechanism must be provided with a clear pass/fail outcome; it is allowed for this to use both the client and server (ie it is not necessary to write any independent mock client or server). In order to support the testing it is allowable to add support for additional commandline arguments or a programmatic interface, for client and/or server.