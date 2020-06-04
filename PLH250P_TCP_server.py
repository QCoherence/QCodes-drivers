import sys
sys.path.append('C:/QCodes drivers and scripts/Drivers')

from PLH250P_current_source_backend import TTi
from PLH250P_current_source_front import current_set,power_up as current_source_on,power_down as current_source_off
current_source = TTi('TTi', 'TCPIP::192.168.0.51::9221::SOCKET')

import socket

import numpy as np

from time import sleep




# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('localhost', 10001)
header='\n\n\n'
header+='############################################\n'
header+='#                                          #\n'
header+='#    TCP server for TTi current source     #\n'
header+='#                                          #\n'
header+='############################################\n'
header+='\n\n\n'
print(header)
print('Starting up server on {} port {}'.format(*server_address))
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
	# Wait for a connection
	print('\n\nwaiting for a connection...')
	connection, client_address = sock.accept()
	try:
		while True:
			data = connection.recv(16)
			# print('\nreceived {!r}'.format(data).decode('ascii'))
			data = data.decode('ascii')
			# sleep(0.1)
			
			if len(data)>0:
				option = data[0]
				if option == '0':
					print('\nreceived power up command')
					try:
						current_source_on(current_source)
					finally:
						print('success')
					connection.sendall(b'success')
				elif option == '1':
					print('\nreceived power down command')
					try:
						current_source_off(current_source)
					finally:
						print('success')
					connection.sendall(b'success')
				elif option == '2':
					value = float(data[2:])
					if data[1] == '1':
						value *= -1
					print('\nreceived set current '+str(value))
					try:
						current_set(current_source,value)
					finally:
						print('success')
					connection.sendall(b'success')
			else:
				break

	finally:
		# Clean up the connection
		connection.close()