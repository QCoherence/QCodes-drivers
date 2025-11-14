# -*- coding: utf-8 -*-
"""
Created on Wed Jul  7 16:44:03 2021

@author: nicolas.roch
"""

import time

import ADwin

n_ramp = 10
# ADC_scale = 0b111111111111111100000000
ADC_offset = 2**23
DAC_offset = 2**15
ad = ADwin.ADwin(DeviceNo=1)
# ad.Boot("./nanoqt/ressources/ADwin11.btl")

ad.Stop_Process(1)
ad.Fifo_Clear(1)
ad.Fifo_Clear(2)

ad.Load_Process("./nanoqt/ressources/acquisition-gold2.TB1")
ad.Start_Process(1)


p0 = [0, 0, 1, 500, 1, 2**15]
p1 = [0, 1, 1, 500, 1, 2**16]
p2 = [0, 1, 1, 500, 1, 0]
ad.SetFifo_Long(1, p0, len(p0))

for i in range(n_ramp):
    ad.SetFifo_Long(1, p1, len(p1))
    ad.SetFifo_Long(1, p2, len(p2))

ad.SetFifo_Long(1, p0, len(p0))

time.sleep(2)
ad.Stop_Process(1)


# measure = np.array(ad.GetFifo_Long(2, int(2*500/1.*n_ramp)))
# measure = (measure-ADC_offset)/ADC_offset*10

# plt.plot(measure, '.')
# plt.show()
