import ADwin

ad = ADwin.ADwin(DeviceNo=1)
# ad.Boot("./nanoqt/ressources/ADwin11.btl")
ad.Load_Process(("./nanoqt/ressources/adwin-detection.TB1"))

print("Process status %f" % ad.Process_Status(1))

ad.Set_Par(1, 2)
print(ad.Get_Par(1))
ad.Start_Process(1)
print("Process status %f" % ad.Process_Status(1))
print(ad.Get_Par(1))
ad.Stop_Process(1)
ad.Set_Par(1, 2)
print("Process status %f" % ad.Process_Status(1))

ad.Start_Process(1)
print("Process status %f" % ad.Process_Status(1))
print(ad.Get_Par(1))
ad.Stop_Process(1)
