import socket
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    


def serial_write(data):

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address = ('localhost', 10000)
#     print('connecting to {} port {}'.format(*server_address))
    sock.connect(server_address)

    try:

        data=str(data)
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



def TCP_pi_write(data):

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address = ('192.168.0.11', 10000)
#     print('connecting to {} port {}'.format(*server_address))
    sock.connect(server_address)

    try:

        data = str(data)
        data = '2:'+data
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