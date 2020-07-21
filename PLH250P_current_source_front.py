# This is wrapper driver with jump protection, and
# can be used to control the instrument, however for 
# simultaneous connections use TCP wrapper.
#                                        -- Arpit

from PLH250P_current_source_backend import setstate,parity
from time import sleep



def current_set(current_source, I):
	I_0=current_source.current()
	steps=int(abs(I_0-I))*10
	for i in range(0,steps):
		current_source.current(I_0+1.0*(I-I_0)*i/steps)
		sleep(0.1)
	current_source.current(I)
	# return steps


def power_up(current_source):
	current_source.current_range('low')
	if current_source.status() == 'off'
		current_source.status('on')
		current_set(current_source, 0)
		setstate('pos')


def power_down(current_source):
	current_set(current_source, 0)
	current_source.status('off')
	setstate('off')