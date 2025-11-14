# -*- coding: utf-8 -*-
"""
Created on Wed Jul  7 16:44:03 2021

@author: nicolas.roch
"""

import ADwin

ad = ADwin.ADwin(DeviceNo=1)
ad.Boot("./nanoqt/ressources/ADwin11.btl")
ad.Stop_Process(1)
ad.Fifo_Clear(1)
ad.Fifo_Clear(2)
ad.Load_Process(("./nanoqt/ressources/acquisition-gold2.TB1"))
ad.Start_Process(1)


p0 = [0, 0, 1, 500, 10, 2**15]
ad.SetFifo_Long(1, p0, len(p0))

ad.Stop_Process(1)
