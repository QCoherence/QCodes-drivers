

import qcodes as qc
from qcodes import (Instrument, VisaInstrument,
                    ManualParameter, MultiParameter,
                    validators as vals)
from qcodes.instrument.channel import InstrumentChannel
from qcodes.instrument.parameter import ParameterWithSetpoints
import numpy as np 
import tqdm.notebook as tqdm
import ADwin 
import time 

FIFO_SZ = 1000000

# class ADwinRamp(ParameterWithSetpoints):
#     def __init__(self, npts)
#     def get_raw(self):

class ADwin_ramp(MultiParameter):

    def __init__(self, 
        name : str, 
        instrument, 
        period: float,
        n_pts:int,  
        N_ramp: int, 
        Vs_high: np.ndarray, 
        Vs_low: np.ndarray,
        progress: bool = False,
        **kwargs) -> None:

        input_number = instrument.get_input_number()

        super().__init__(name, 
            instrument = instrument,
            names =  tuple(f"Input_{e+1}" for e in input_number),
            units = tuple("V" for e in input_number), 
            shapes = tuple((n_pts*N_ramp,) for e in input_number),
            setpoint_units = tuple(("pts",) for e in input_number),
            # setpoints = tuple((np.array(range(N_ramp*n_pts)), ) for e in input_number),
            setpoint_labels = tuple((f"Input {e+1} points",) for e in input_number),
            setpoint_names = tuple((f"input_{e+1}_points",) for e in input_number), 

        )

        self.period = period
        self.half_period= 0.5*period
        self.n_pts = n_pts
        self.N_ramp = N_ramp
        self.Vs_high = Vs_high
        self.Vs_low = Vs_low
        self.progress = progress

    def generate_outs_targets(self):
        output_number = len(self.instrument.get_output_number())
        #max_adwin_ramp_time = 2**16*self.instrument.process_duration # What ? Change this 
        max_adwin_ramp_time = FIFO_SZ * self.instrument.process_duration
        outs_array = []
        for i in range(output_number):
            out = []
            for n in range(self.N_ramp):
                
                if self.half_period < max_adwin_ramp_time:
                    # self.instrument.ramp_size(self.n_pts//2)
                    self.instrument.ramp_size(int(self.period/self.instrument.process_duration) )
                    self.instrument.subsampling(2*int(self.instrument.ramp_size()/self.n_pts))
                    out.append(np.array([self.Vs_high[i]]))
                    out.append(np.array([self.Vs_low[i]]))
                    
                else :
                    subdivision = self.half_period//max_adwin_ramp_time
                    out.append(np.linspace(self.Vs_low[i], self.Vs_high[i],
                                            num=int(subdivision)+2)[1:])
                    out.append(np.linspace(self.Vs_high[i], self.Vs_low[i],
                                            num=int(subdivision)+2)[1:])

                    self.instrument.ramp_size(int(self.half_period/(subdivision+1)/5e-6) )
                    self.instrument.subsampling(2*int(((subdivision+1)*self.instrument.ramp_size())/self.n_pts))
            outs_array.append(np.concatenate(out))
        
        return np.stack(outs_array)
                
            


    def get_raw(self):
        outs_array = self.generate_outs_targets()
        
        input_number = len(self.instrument.get_input_number())
        inputs = np.zeros(shape=(input_number,0))
        loop_range = range(outs_array.shape[1]) if not self.progress else tqdm.tqdm(range(outs_array.shape[1]))

        # Go to the lower value before starting
        self.instrument.outputs(np.array(self.Vs_low))
        self.instrument.set_outputs_one_cycle()
        _ = self.instrument.inputs.get()
        #Wait for 0.1 sec before starting the loops
        time.sleep(0.1)


        for i in loop_range:
            self.instrument.outputs(outs_array[:,i])
            self.instrument.launch_measurement()
            meas = self.instrument.inputs.get()
            # print(meas[::4] == meas[2::4])
            meas = np.transpose(np.reshape(meas, (meas.shape[0]//input_number, input_number)))
            inputs = np.concatenate([inputs, meas], axis=1)




        self.shapes = tuple((inputs.shape[1],)  for e in range(input_number))
        self.setpoints = tuple((np.array(range(inputs.shape[1])), ) for e in range(input_number))
        self.instrument.go_to_zero()
        return inputs


class ADwin_averagedRamp(MultiParameter):

    def __init__(self, 
        name : str, 
        instrument, 
        period: float, # Period in seconds
        n_pts:int,     # Number of points measured in one period (up ramp and down ramp)
        N_ramp: int,   # Number of ramps
        Vs_high: np.ndarray,  # "High values" of the ramps in volts these can be negative if you want to do the down ramp before the up ramp
        Vs_low: np.ndarray,   # "Low values" of the ramps in volts
        progress: bool = False,
        **kwargs) -> None:

        input_number = instrument.get_input_number()
        doubled_input_number_list = sorted(2*input_number) # double the occurence of each input number to label the up/down part of the ramp
        super().__init__(name, 
            instrument = instrument,
            names =  tuple(f"Input_{e+1}_{'down' if i%2 else 'up'}" for i, e in enumerate(doubled_input_number_list)),
            units = tuple("V" for e in doubled_input_number_list), 
            shapes = tuple((n_pts,) for e in doubled_input_number_list),
            setpoint_units = tuple(("pts",) for e in doubled_input_number_list),
            # setpoints = tuple((np.array(range(N_ramp*n_pts)), ) for e in input_number),
            setpoint_labels = tuple((f"Input {e+1} {'down' if i%2 else 'up'} ramp points",) for i, e in enumerate(doubled_input_number_list)),
            setpoint_names = tuple((f"input_{e+1}_{'down' if i%2 else 'up'}_points",) for i, e in enumerate(doubled_input_number_list)), 

        )
        self.period = period
        self.half_period= 0.5*period
        self.n_pts = n_pts
        self.N_ramp = N_ramp
        self.Vs_high = Vs_high
        self.Vs_low = Vs_low
        self.progress = progress

    def generate_outs_targets(self):
        output_number = len(self.instrument.get_output_number())
        #max_adwin_ramp_time = 2**16*self.instrument.process_duration #
        #max_adwin_ramp_time = FIFO_SZ * self.instrument.process_duration ## This is not the good metric, TODO: change that to use the number of pts < FIFO_SZ
        max_adwin_nb_pts = FIFO_SZ # Since FIFO_SZ is smaller than the long format (32 bits)
        outs_array = []
        for i in range(output_number):
            out = []
            for n in range(self.N_ramp):
                
                #if self.half_period < max_adwin_ramp_time:
                if self.n_pts <= max_adwin_nb_pts:
                    # self.instrument.ramp_size(self.n_pts//2)
                    self.instrument.ramp_size(int(round(self.period/self.instrument.process_duration) ))
                    self.instrument.subsampling(2*int(round(self.instrument.ramp_size()/self.n_pts)))
                    out.append(np.array([self.Vs_high[i]]))
                    out.append(np.array([self.Vs_low[i]]))
                                        
                else :
                    ## This is sketchy it needs to be clarified TODO: double check the splitting of the ramps
                    subdivision = self.n_pts//max_adwin_nb_pts
                    out.append(np.linspace(self.Vs_low[i], self.Vs_high[i],
                                            num=int(subdivision)+2)[1:])
                    out.append(np.linspace(self.Vs_high[i], self.Vs_low[i],
                                            num=int(subdivision)+2)[1:])

                    self.instrument.ramp_size(int(self.period/self.instrument.process_duration) )
                    self.instrument.subsampling(2*int(((subdivision+1)*self.instrument.ramp_size())/self.n_pts))
            outs_array.append(np.concatenate(out))
        
        return np.stack(outs_array)
                

    def get_raw(self):
        outs_array = self.generate_outs_targets()
        
        input_number = len(self.instrument.get_input_number())
        inputs = np.zeros(shape=(input_number,0))
        loop_range = range(outs_array.shape[1]) if not self.progress else tqdm.tqdm(range(outs_array.shape[1]))

        # Go to the lower value before starting
        self.instrument.outputs(np.array(self.Vs_low))
        self.instrument.set_outputs_one_cycle()
        #_ = self.instrument.inputs.get()
        self.instrument.clear_fifos()
        # #Wait for 0.1 sec before starting the loops
        #time.sleep(0.1)
        expected_size = self.instrument.ramp_size() // self.instrument.subsampling()
        for i in loop_range:
            self.instrument.outputs(outs_array[:,i])
            self.instrument.launch_measurement()

            while self.instrument.device.Fifo_Full(2) < expected_size:
                time.sleep(10*self.instrument.process_duration)

            meas = self.instrument.inputs.get()
            
            meas = np.transpose(np.reshape(meas, (meas.shape[0]//input_number, input_number)))
            inputs = np.concatenate([inputs, meas], axis=1)



        inputs = np.reshape( inputs , (inputs.shape[0], self.N_ramp, inputs.shape[1]//self.N_ramp))
        inputs = np.mean(inputs, axis=1)
        split_inputs = np.array_split(inputs, 2, axis=1)
        # split_inputs = np.concatenate(split_inputs)
        split_inputs = list(split_inputs[0]) + list(split_inputs[1])

        rearranged=[]
        for e in range(inputs.shape[0]):
            rearranged.append(e)
            rearranged.append(e+inputs.shape[0])
        split_inputs = [split_inputs[i] for i in rearranged]


        self.shapes = tuple((len(split_inputs[e]),)  for e in range(len(split_inputs)))
        self.setpoints = tuple((np.array(range(len(split_inputs[e]))), ) for e in range(len(split_inputs)))
        self.instrument.go_to_zero()

        return split_inputs

class ADwin_IV(MultiParameter):
    def __init__(self, 
        name: str, 
        avgRamp: ADwin_averagedRamp,
        voltage_input: int, 
        current_input: int,
        voltage_divider_value:float, 
        current_coefficient:float):

        if not isinstance(avgRamp, ADwin_averagedRamp):
            raise Exception("The parameter avgRamp should be a ADwin_averagedRamp parameter")

        if len(avgRamp.instrument.get_input_number())!=2:
            raise Exception(f"The Adwin should be measuring exactly two inputs for the IV (found {len(avgRamp.instrument.get_input_number())} inputs)")



        super().__init__(name, 
                instrument = avgRamp.instrument,
                names = ('up_ramp', 'down_ramp'),
                units = ('A', 'A') ,
                shapes = ((avgRamp.n_pts,),(avgRamp.n_pts,)) ,
                setpoint_units = (('V',), ('V',)),
                # setpoints = tuple((np.array(range(N_ramp*n_pts)), ) for e in input_number),
                setpoint_labels = ((f"ADwin input {voltage_input} up ramp",), (f"ADwin input {voltage_input} up ramp",)),
                setpoint_names = ((f"input_{voltage_input}_voltage_up",), (f"input_{voltage_input}_voltage_down",)),
                metadata = {'Voltage divider value' : "%.2e" %  voltage_divider_value, 'Current coefficient': "%.2e" % current_coefficient}
                ) 

        self.avgRamp= avgRamp

        self.voltage_input = voltage_input
        self.current_input = current_input
        self.VD = voltage_divider_value
        self.IC = current_coefficient

    def get_raw(self):
        ad_inputs = self.avgRamp.get_raw()
        x1 = 0 if self.voltage_input > self.current_input else 2
        x2 = 2 if self.voltage_input > self.current_input else 0


        self.shapes = ((len(ad_inputs[x1]), ),   (len(ad_inputs[x1+1]), ) )
        self.setpoints = ((ad_inputs[x2]/self.VD,), (ad_inputs[x2+1]/self.VD,))

        return [ad_inputs[x1]/self.IC, ad_inputs[x1+1]/self.IC]


class ADwin_VI(MultiParameter):
    #Measuring the voltage and biasing in current
    def __init__(self, 
        name: str, 
        avgRamp: ADwin_averagedRamp,
        voltage_input: int, 
        current_input: int,
        current_divider_value:float, 
        voltage_coefficient:float):

        if not isinstance(avgRamp, ADwin_averagedRamp):
            raise Exception("The parameter avgRamp should be a ADwin_averagedRamp parameter")

        if len(avgRamp.instrument.get_input_number())!=2:
            raise Exception(f"The Adwin should be measuring exactly two inputs for the VI (found {len(avgRamp.instrument.get_input_number())} inputs)")



        super().__init__(name, 
                instrument = avgRamp.instrument,
                names = ('up_ramp', 'down_ramp'),
                units = ('V', 'V') ,
                shapes = ((avgRamp.n_pts,),(avgRamp.n_pts,)) ,
                setpoint_units = (('A',), ('A',)),
                # setpoints = tuple((np.array(range(N_ramp*n_pts)), ) for e in input_number),
                setpoint_labels = ((f"ADwin input {voltage_input} up ramp",), (f"ADwin input {voltage_input} up ramp",)),
                setpoint_names = ((f"input_{voltage_input}_voltage_up",), (f"input_{voltage_input}_voltage_down",)),
                metadata = {'Current divider value' : "%.2e" %  current_divider_value, 'Voltage coefficient': "%.2e" % voltage_coefficient}
                ) 

        self.avgRamp= avgRamp

        self.voltage_input = voltage_input
        self.current_input = current_input
        self.CD = current_divider_value
        self.VC = voltage_coefficient

    def get_raw(self):
        ad_inputs = self.avgRamp.get_raw()
        x1 = 0 if self.voltage_input < self.current_input else 2
        x2 = 2 if self.voltage_input < self.current_input else 0


        self.shapes = ((len(ad_inputs[x1]), ),   (len(ad_inputs[x1+1]), ) )
        self.setpoints = ((ad_inputs[x2]/self.CD,), (ad_inputs[x2+1]/self.CD,))

        return [ad_inputs[x1]/self.VC, ad_inputs[x1+1]/self.VC]





class ADwin_Gold2(Instrument): 
    
    """
    QCoDeS driver for the ADwin Gold II
    """
    
    # all instrument constructors should accept **kwargs and pass them on to
    # super().__init__

    def __init__(self, name, boot_file, process_file, adwin_no=1, **kwargs):
        # supplying the terminator means you don't need to remove it from every response
        super().__init__(name, **kwargs)

        self.bf = boot_file 
        self.pf = process_file 
        self.subs = 1
        self.rs = 1000 #ramp size
        self._output_mask = 0b1
        self._input_mask = 0b1
        self._adwin_mode = 0b0

        self.add_parameter( name='adwin_mode',
                            label='Adwin mode',
                            vals = vals.Numbers(0x0, 0x20000),
                            unit='',
                            set_cmd=self.set_mode,
                            get_cmd=self.get_mode
        )

        
        self.add_parameter( name = 'ramp_size',  
                            label = 'Size for all the ramps of the ADwin',
                            vals = vals.Numbers(0, FIFO_SZ),
                            unit   = 'pts',
                            set_cmd=self.set_ramp_size,
                            get_cmd=self.get_ramp_size
                            )

        self.add_parameter(name = 'fifo_size',
                            label= 'Size of the total input fifo',
                            vals= vals.Numbers(0,8*2**16),
                            get_cmd= self.get_input_size,
                            set_cmd = None
                            )

        self.add_parameter( name = 'subsampling',  
                            label = 'Subsampling factor for the ADwin',
                            vals = vals.Numbers(0, 2**16),
                            unit   = '',
                            set_cmd=self.set_subsampling,
                            get_cmd=self.get_subsampling
                            )

        self.add_parameter(name = 'output_mask',
                            label= 'Output mask in the FIFO',
                            vals= vals.Numbers(0b1,0b11111111),
                            unit= '',
                            set_cmd=self.set_output_mask,
                            get_cmd=self.get_output_mask)
        self.add_parameter(name = 'input_mask',
                            label= 'Input mask in the FIFO',
                            vals= vals.Numbers(0b1,0b11111111111111),
                            unit='',
                            set_cmd=self.set_input_mask,
                            get_cmd=self.get_input_mask)

        self.add_parameter( name = 'outputs',  
                            label = 'Outputs of the ADwin',
                            vals = vals.Arrays(-10,10),
                            unit   = 'V',
                            set_cmd=self.set_outputs,
                            get_cmd='',
                            set_parser = lambda x: np.array(list(map(self.volt_to_binary, x))),
                            get_parser= lambda x: np.array(list(map(self.binary_to_volt, x)))
                            )


        self.add_parameter( name = 'inputs',  
                            label = 'Inputs of the ADwin',
                            vals = vals.Arrays(-10,10, shape=(self.get_input_size ,)),
                            unit = 'V',
                            set_cmd='',
                            get_cmd=self.read_inputs,
                            get_parser= lambda x: np.array(list(map(self.binary_to_volt, x)))
                            )
        
        self.add_parameter(name='lockin_freq',
                           label='Lock in frequency in Hz',
                           unit='Hz',
                           set_cmd= lambda x: self.device.Set_FPar(1, x), 
                           get_cmd= lambda : self.device.Get_FPar(1),
                           set_parser = lambda x: (x*2*np.pi*self.process_duration),
                           get_parser = lambda x: np.round(x/2/np.pi/self.process_duration, 4)
                           )
        
        self.add_parameter(name='lockin_amplitude',
                           label= 'Lock in amplitude in volts',
                           unit='V',
                           set_cmd= lambda x: self.device.Set_FPar(2, x),
                           get_cmd= lambda : self.device.Get_FPar(2),
                           set_parser = self.volt_to_binary,
                           get_parser = self.binary_to_volt_lockin,
                            )
        

        
    

        self.device = ADwin.ADwin(adwin_no)
        self.boot_load()
        self.process_load()
        self.clear_fifos()

        # good idea to call connect_message at the end of your constructor.
        # this calls the 'IDN' parameter that the base Instrument class creates 
        # for every instrument  which serves two purposes:
        # 1) verifies that you are connected to the instrument
        # 2) gets the ID info so it will be included with metadata snapshots later.
        self.connect_message()

    def boot_load(self):
        """Load the boot binary on the ADwin"""
        self.device.Boot(self.bf)
    
    def process_load(self):
        """Load the process binary on the ADwin and set the Process Delay to 10 us (for a T11 processor !)"""
        self.device.Stop_Process(1)
        self.device.Load_Process(self.pf)
        
        self.device.Set_Processdelay(1, 3000) # Setting the process frequency to 100 kHz since the clock of the T11 is 3.33 ns
        self.process_duration = 10e-9/3.0 * 3000 # The process duration is thus 10 us
        self.device.Start_Process(1)

    def volt_to_binary(self, V):
        """Convert the voltage given to the binary representation for the DAC"""
        return int(V/10*2**15 + 2**15)
    
    def binary_to_volt_lockin(self, B):
        """Convert back the binary value of the lockin amplitude"""
        return float((B-2**15)/2**15 * 10)

    def binary_to_volt(self, B):
        """Convert back the binary of the ADC to a voltage between -10V and +10V"""
        return (B-2**23)/2**23*10

    def set_outputs(self, targets: np.array):
        '''Creating the FIFO to send to the ADWIN, 
        The ADwin will ramp to the point in phase space R^(max number of outputs=8) specified by the argument "targets"
        it will start from its current position in this space (it will not reset the outputs to 0V)
        all outputs not targeted by the output mask will not change and stay at their current values.
        -------------
        FIFO parameters:
        FIFO[0]= Mode of the ADwin in binary (0b0 is default, 0b10000 is Lock_in, all the modes bits can be found in the acquisition.bas file at C:/Users/nicolas.roch/Measurements/Drivers/adwin/nanoqt/ressources
        FIFO[1]= Input mask in binary, for example 0b1101 yields a measurement on input 1, 3 and 4; 0b1010 on inputs 2 and 4
        FIFO[2]= Output mask in binary same as the input mask, for example 0b111 will mean that the ADwin will change outputs 1, 2 and 3
        FIFO[3]= The number of points in the ramp yielding the total time for the ramp via T (in seconds)= nb_pts/(100 kHz) 
        FIFO[4]= Subsampling for the inputs, for a given subsampling rate S: every S process duration (every S/(100 kHz) seconds) the ADwin will measure the inputs specified in the input mask variable
        FIFO[5 to last]= The target voltages, in binary, for each outputs specified in the output mask variable
        -------------
        '''

        self.fifo_list = [self.adwin_mode(), self.input_mask(), self.output_mask(), self.ramp_size(), self.subsampling()]

        for t in targets:
            self.fifo_list.append(t)
        # inputs_number = bin(self.input_mask).count('1') #count the number of 1 in input_mask by converting it to string and using .count (horrible but whatever)
        # self.values_in_fifo += int(self.rs/self.subs*inputs_number)

    def set_outputs_one_cycle(self):
        '''Set the outputs in one process cycle instead of waiting'''
        old_rs = self.fifo_list[3]
        self.fifo_list[3] = 1
        self.device.SetFifo_Long(1, self.fifo_list, len(self.fifo_list))

        time.sleep(2*self.process_duration) # Wait two process durations (20us)
        self.fifo_list[3] = old_rs


    def launch_measurement(self):
        self.device.SetFifo_Long(1, self.fifo_list, len(self.fifo_list))
        time.sleep(self.ramp_size() * self.process_duration)

    def go_to_zero(self):
        old_om = self.output_mask()
        self.output_mask(0b11111111)
        # targets = np.array(list(map(self.volt_to_binary, [0.0]*8)))
        # self.set_outputs(targets)
        self.outputs(np.array([0.0]*8))
        self.set_outputs_one_cycle()
        self.output_mask(old_om)
        self.clear_fifos()

    def read_inputs(self):
        '''Read all the values in the measurement FIFO at once'''
        # self.device.SetFifo_Long(1, self.fifo_list, len(self.fifo_list))
        # time.sleep(self.rs / 40e5)
        M_size = self.device.Fifo_Full(2)
        arr = np.array(self.device.GetFifo_Long(2, int(M_size)))
        return arr 

    def clear_fifos(self):
        '''Clear the two FIFO used on the ADwin'''
        self.device.Fifo_Clear(1)
        self.device.Fifo_Clear(2)

    def get_input_size(self):
        inputs_number = bin(self.input_mask()).count('1') #count the number of 1 in input_mask by converting it to string and using .count (horrible but it works)
        M_size = int(self.ramp_size()/self.subsampling()*inputs_number)
        return M_size

    def get_input_number(self):
        raw_string = bin(self.input_mask())[2:][::-1]
        names = []
        for i_number, l in enumerate(raw_string):
            if int(l) == 1:
                names.append(i_number)
        return names
    
    def get_output_number(self):
        raw_string = bin(self.output_mask())[2:][::-1]
        names = []
        for i_number, l in enumerate(raw_string):
            if int(l) == 1:
                names.append(i_number)
        return names

    def get_input(self):
        """Get one value from the measure FIFO on the ADwin"""
        return list(self.device.GetFifo_Long(2, 1))[0]

    def set_mode(self, mode):
        self._adwin_mode = mode 
        
    def get_mode(self):
        return self._adwin_mode
    
    def set_ramp_size(self, rs):
        """Set internal ramp time in numbers of points"""
        self.rs = rs
    
    def get_ramp_size(self):
        """Get internal ramp time in numbers of points"""
        return self.rs

    def set_output_mask(self, mask):
        """Set the ouput mask in binary form"""
        self._output_mask = mask
    
    def get_output_mask(self):
        """Get the ouput mask in binary form"""
        return self._output_mask

    def set_input_mask(self, mask):
        """Set the input mask in binary form"""
        self._input_mask = mask
    
    def get_input_mask(self):
        """Get the input mask in binary form"""
        return self._input_mask

    def set_subsampling(self, subsampling):
        """Set subsampling factor"""
        self.subs = subsampling
    
    def get_subsampling(self):
        """Get subsampling factor"""
        return self.subs
    
    def get_idn(self):
        """Return a dictionnary with the informations on the instrument"""
        output = {}
        output['vendor'] = 'ADwin'
        output['model'] = 'ADwin_GOLD2'
        output['test_version'] = self.Test_Version()
        return output 

    def Test_Version(self):
        return 'bybass'
        


def adwin_Nramp(ad: ADwin_Gold2, start_pt, end_pt, ramp_size0, nb_ramps):
    ad.out1(start_pt)
    ad.device.Fifo_Clear(1)
    ad.device.Fifo_Clear(2)

    ad.ramp_size(ramp_size0)
    for i in range(nb_ramps):
        ad.out2(end_pt)
        ad.out2(start_pt) 
    

    time.sleep(ramp_size0*1e-5*2*nb_ramps+1)
    M_size = ad.device.Fifo_Full(2)
    arr = []
    for i in range(int(M_size)):
        arr.append(ad.in1.get())
    return arr