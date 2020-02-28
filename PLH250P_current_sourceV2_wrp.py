



def current_set(current_source, I):
	I_0=current_source.current()
	steps=1+int(abs(I_0-I))*10
	for i in range(0,steps):
		current_source.current(I_0+1.0*(I-I_0)*i/steps)
	current_source.current(I)