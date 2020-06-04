# This is TCP wrapper driver with jump protection, and
# should be used to control the instrument.
#                                        -- Arpit

import socket
import sys


def ret_sign(I):
	if I<0:
		ret = 1
	else:
		ret = 0
	return ret


def current_set(I):
	# Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address = ('localhost', 10001)
#     print('connecting to {} port {}'.format(*server_address))
    sock.connect(server_address)

    sign = ret_sign(I)

    try:

        data=str(2)+str(sign)+str(abs(I))
        # Send data
        message = data.encode()
        sock.sendall(message)

        # Look for the response

        data = sock.recv(16)
        if data.decode('ascii')!='success':
            print('### ERROR: receipt confirmation not received from serial server.')

    finally:
#         print('closing socket')
        sock.close()


def power_up():
	# Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address = ('localhost', 10001)
#     print('connecting to {} port {}'.format(*server_address))
    sock.connect(server_address)

    try:

        data=str(0)
        # Send data
        message = data.encode()
        sock.sendall(message)

        # Look for the response

        data = sock.recv(16)
        if data.decode('ascii')!='success':
            print('### ERROR: receipt confirmation not received from serial server.')

    finally:
#         print('closing socket')
        sock.close()


def power_down():
	# Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address = ('localhost', 10001)
#     print('connecting to {} port {}'.format(*server_address))
    sock.connect(server_address)

    try:

        data=str(1)
        # Send data
        message = data.encode()
        sock.sendall(message)

        # Look for the response

        data = sock.recv(16)
        if data.decode('ascii')!='success':
            print('### ERROR: receipt confirmation not received from serial server.')

    finally:
#         print('closing socket')
        sock.close()