import socket
import sys

import serial
import time
ser = serial.Serial('COM5', 9600, timeout=2)

def serial_write(num):
	# print('num is:',num)
	repeat=True
	while repeat:
		time.sleep(0.5)
		# print('r1')
		ser.write(str(num).encode())
		# print('r2')
		read=ser.read(1)
		# print('read: ',read.decode('ascii'))#,toBinary(str(num)))
		# print('r3')
		if read.decode('ascii')==str(num):
			repeat=False

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('localhost', 10000)
header='\n\n\n'
header+='############################################\n'
header+='#                                          #\n'
header+='#       TCP server for arduino @ COM5      #\n'
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
    print('\nwaiting for a connection...')
    connection, client_address = sock.accept()
    try:
        while True:
            data = connection.recv(16)
            # print('\nreceived {!r}'.format(data).decode('ascii'))
            if data:
                print('\nreceived',data.decode('ascii'))
                print('sending data to arduino...')
                data=data.decode('ascii')
                serial_write(data)
                print('success')
                connection.sendall(b'success')
            else:
                break

    finally:
        # Clean up the connection
        connection.close()