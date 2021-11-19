# This is TCP wrapper driver with jump protection and
# current limit, and should be used to control the 
# instrument.
#                                        -- Arpit

import socket
import sys

I_limit = 30


def ret_sign(I):
	if I<0:
		ret = 1
	else:
		ret = 0
	return ret


def current_set(I):

	if abs(I) <= I_limit:

		# Create a TCP/IP socket
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# Connect the socket to the port where the server is listening
		server_address = ('localhost', 10001)
		# print('connecting to {} port {}'.format(*server_address))
		sock.connect(server_address)

		sign = ret_sign(I)

		try:

			data=str(2)+str(sign)+str(round(abs(I),2))
			# Send data
			message = data.encode()
			sock.sendall(message)

			# Look for the response

			data = sock.recv(16)
			if data.decode('ascii')!='success':
				print('### ERROR: receipt confirmation not received from serial server.')

		finally:
			# print('closing socket')
			sock.close()

	else:

		print('Error : current above safety limit ('+str(I_limit)+' mA)')


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