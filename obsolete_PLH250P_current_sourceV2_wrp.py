from PLH250P_current_sourceV2 import setstate
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
	current_set(current_source, 0)
	current_source.status('on')
	setstate('pos')



def power_down(current_source):
	current_set(current_source, 0)
	current_source.status('off')
	setstate('off')