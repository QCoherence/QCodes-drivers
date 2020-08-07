#-*-coding utf8-*-

#Import classic modules
import numpy as np
import matplotlib
import matplotlib.pyplot as plt



def fill_2D_memory(function, parameters, trigger=('NONE')):
        """
        Fill a 2D memory.
        First version with 1 repetion of chunks of 8 values.
        Input:
                function(string): name of the function
                parameters(float): vector of parameters characterizing the function:
                freq (Hz), Amplitude (from 0 to 1), pulse_duration (s), delay (s)
        Output:
                the 2D table (int)
        """
        if function=='SIN':

            freq, amplitude, pulse_duration, delay = parameters
            # the size of the memory is 65536 and the time step pf the DACS is
            # 500 ps
            if freq > 1./0.5e-9 or amplitude > 1 or pulse_duration + delay > 64.e-6:
                raise ValueError('One of the parameters is not correct')

            else :
                if freq > 1./(4.*0.5e-9):
                    print('Warning : bellow 4 points per period, the signal might be unstable.')

                DAC_amplitude = amplitude * 8192 # DAC values are coded on signed 14 bits = +/- 8192
                N_point = int(round(pulse_duration/0.5e-9))

                N_point_tot=int(round((pulse_duration+delay)/0.5e-9))

                n_oscillation = freq*pulse_duration
                t = np.linspace(0, 2 * np.pi,N_point)

                table=DAC_amplitude*np.concatenate((np.zeros(int(round(delay/0.5e-9))),np.sin(n_oscillation*t),np.zeros(N_point%8)))

                # we add zeros at the end so that N_point_tot is dividable by 8
                # because the tible is to be divided in chunks of 8 values
                table=table.reshape(int(round(table.shape[0]/8.)),8)

                memory_table=np.concatenate((table,np.zeros((table.shape[0],1)),np.zeros((table.shape[0],2))),axis=1)

                # the triggers of one channel are stored in a tuple
                # the tuple is composed of couples of string for the trigger val
                # and float for the time at wich a trigger is set
                # by default trigger is set to none and all trigger is set to 0

                if trigger == 'NONE':

                    return memory_table.reshape((1,memory_table.shape[0]*memory_table.shape[1]))[0]

                else :
                    for trig in trigger :

                        trig_name=trig[0]
                        trig_time=trig[1]
                        trig_row_index=int(round(trig_time/(0.5e-9 * 8)))

                        if trig_name=='TRIG1':
                            memory_table[trig_row_index,-1]=1.
                        elif trig_name=='TRIG2':
                            memory_table[trig_row_index,-2]=1.
                        elif trig_name=='BOTH':
                            memory_table[trig_row_index,-1]=1.
                            memory_table[trig_row_index,-2]=1.
                        else :
                            raise ValueError('Wrong trigger value')

                    return memory_table.reshape((1,memory_table.shape[0]*memory_table.shape[1]))[0]



def reset_DAC_2D_memory(channel):
    """
        Reset the 2D memory of one DAC by filling with zeros and the end of table instruction

        Input : - channel of the DAC we wantto reset

        Output : - SCPI instruction for filling the DAC memory is re initialized table
    """

    pass







def send_DAC_2D_memory(table, channel, duration=0,mode='pulses'):

        #THIS FUNCTION CAN BE WRITTEN IN A NICER MANNER USING ARGS AND KWARGS
        #BCSE DURATION AND MODE ARE  SYSTEMATICALLY USED

        """
            Send a 2D memory to one of the DAC chanels

            Input : - table (float): table to be sent
                    - channel(string): channel in which to table in sent
                    - adress(string): adress in the table of the DAC at which
                                      we start to write

        """
        # self.log.info(__name__+ ' Send the 2D memory to DAC'+ channel+'  \n')

        # convert the element of table_bit to int and then to string for sending
        # then forming a whole string with values separated by commas by using
        # the join method
        table_bit=(table.astype(int)).astype(str)
        separator = ','
        table_bit = separator.join(table_bit)

        if channel in ['CH1','CH2','CH3','CH4','CH5','CH6','CH7','CH8']:

            if mode == 'pulses':
                # self.write('DAC:DATA:'+channel+' '+adress+','+table_bit)

                return 'DAC:DATA:'+channel+' '+'0'+','+table_bit+','+'0,0,0,0,0,0,0,0,0,0,16383'

            elif mode == 'CW':

                adress = int(round(16384 - duration/(4.e-9)))

                return 'DAC:DATA:'+channel+' '+str(adress)+','+table_bit

            else :
                raise ValueError('Wrong mode value')

        else:
            raise ValueError('Wrong channel value')


def ADC_status(ADC_list):

    dec=0

    for ADCnum in ADC_list:
        dec+=2**(ADCnum+23)

    return dec

def DAC_status(DAC_list):

    dec=0

    for DACnum in DAC_list:
        dec+= 2**(3*DACnum - 3) + 2**(3*DACnum - 2) + 0*2**(3*DACnum - 1)

    return dec



def ADC_DAC_status(DAC_list, ADC_list):

    return str(DAC_status(DAC_list)+ADC_status(ADC_list))


def get_data():

    pass


if __name__ == "__main__":

    freq=1.e6
    amp=1.
    pulse_duration=1.1e-6
    delay=0.
    trigger='NONE'

    param=[freq,amp,pulse_duration,delay]

    mem2D=fill_2D_memory('SIN',param,trigger)

    serv=send_DAC_2D_memory(mem2D,'CH2',pulse_duration)
