# This module opens COM line to arduino over USB and serves as base 
# communication layer for current controller and MW switch controller.
#                                                            -- Arpit

import serial
import time
ser = serial.Serial('COM4', 9600, timeout=2)






def serial_write(num):
	print('num is:',num)
	repeat=True
	while repeat:
		time.sleep(0.5)
		# print('r1')
		ser.write(str(num).encode())
		# print('r2')
		read=ser.read(1)
		print('read: ',read.decode('ascii'))#,toBinary(str(num)))
		# print('r3')
		if read.decode('ascii')==str(num):
			repeat=False