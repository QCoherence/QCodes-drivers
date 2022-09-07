	def get_readout_pulse(self):

		'''

		 This function reformat the data without looping over all the headers by trusting that 
		 what we set is what we get.
		 It also assumes that within a sequence every ADC pulses have the same length.

		'''

		self.reset_output_data()

		#for now we consider only the one same type of acq on all adc
		mode=self.acquisition_mode.get()

		nb_measure=self.nb_measure.get()

		length_vec,ch_vec=self.adc_events()
		
		N_adc_events=len(ch_vec)
		N_acq=np.sum(np.sum(length_vec))
		
		#same acquisition length for all ADCs
		N_acq_single=int(round(N_acq/N_adc_events))

		 
		# 8 I and Q channels
		adcdataI = [[],[],[],[],[],[],[],[]]
		adcdataQ = [[],[],[],[],[],[],[],[]]

		tstart = time.perf_counter()
		tick = 0.1
		duree = 2

		rep=[]
		count_meas=0
		end_loop=0

		if mode=='SUM':

			self.write("SEQ:START")
			time.sleep(0.1)

			while (count_meas//(16*N_adc_events))<self.nb_measure.get():

				start_time = datetime.datetime.now()
				r = self.ask('OUTPUT:DATA?')
				step_time = datetime.datetime.now()
				print('get data',len(r)//(16000*N_adc_events),str(step_time-start_time))

				if r == 'ERR':

					log.error('rfSoC: Instrument returned ERR!')

					break

				elif len(r)>1:

					empty_packet_count = 0

					rep = rep+r
					step_time = datetime.datetime.now()
					print('add data',str(step_time-start_time))

					count_meas+=len(r)


				elif r==[3338]:

					empty_packet_count += 1
					print('got empty')
					time.sleep(0.1)

				if empty_packet_count>20:

					log.warning('Data curruption: rfSoC did not send all data points({}).'.format(count_meas//(16*N_adc_events)))

					break

			

		if mode=='RAW':

			self.write("SEQ:START")
			time.sleep(0.1)


			while end_loop==0:
				time.sleep(0.5)
				r = self.ask('OUTPUT:DATA?')

				if len(r)>1:
					# print(len(r))
					rep = rep+r
					
					#to modify manually depending on what we
					#TODO : figure a way to do it auto depending on the adcs ons and their modes
					#now for 1 ADC in accum
					# count_meas+=len(r)//16
					count_meas+=len(r)//((8+N_acq))


				elif r==[3338]:

					# count_meas=nb_measure
					# count_meas=1
					end_loop = 1


		# while time.perf_counter()<(tstart+duree):

		#     time.sleep(tick)
		#     r = self.ask('OUTPUT:DATA?')
		#     if len(r)>1:
		#         rep = rep+r

		self.write("SEQ:STOP")
		#we ask for last packet and add it
		r = self.ask('OUTPUT:DATA?')
		if len(r)>1:
				rep = rep+r

		rep=np.array(rep,dtype=int)
		# np.save('raw_IQ_data_dump_'+str(self.nb_measure.get()),rep)

		#data decoding
		if mode is 'RAW':

			# removing headers

			mask = np.ones(len(rep), dtype=bool) #initialize array storing which items to keep

			starts = np.arange(0, len(rep), N_acq_single + 8)
			#print(starts)
			indices=np.arange(8) + starts[:,np.newaxis] #indeces of headers datapoints
			indices=indices.flatten()
			#print(indices)
			mask[indices]=False

			res=np.right_shift(rep[mask],4)*(2*0.3838e-3)

			res=np.split(res,nb_measure)

			res=np.mean(res,axis=0)

			res=np.split(res,N_adc_events)

			for i in range(len(ch_vec)):

				adcdataI[ch_vec[i]].append(res[i])


		if mode is 'SUM':

			# removing headers

			mask = np.ones(len(rep), dtype=bool) #initialize array storing which items to keep

			starts = np.arange(0, len(rep), 8 + 8)

			indices=np.arange(8) + starts[:,np.newaxis] #indices of headers datapoints
			indices=indices.flatten()

			mask[indices]=False

			res=rep[mask]
			# print('count_meas={}'.format(count_meas))
			# print('nb_measure={}'.format(nb_measure))
			# print('len(res)={}'.format(len(res)))

			#format for unpacking
			fmt='q'*nb_measure
	   
			for i in range(len(ch_vec)):

				maskI= np.zeros(len(res), dtype=bool) #initialize array storing which items to keep
				maskQ= np.zeros(len(res), dtype=bool) #initialize array storing which items to keep

				starts= np.arange(8*i,len(res), len(ch_vec)*8 )

				indicesI=np.arange(4) + starts[:,np.newaxis]
				
				indicesI=indicesI.flatten()

				indicesQ=np.arange(4) + starts[:,np.newaxis] 
				indicesQ=indicesQ.flatten() + 4    

				maskI[indicesI]=True
				maskQ[indicesQ]=True

				newI=res[maskI].astype('int16').tobytes()
				newQ=res[maskQ].astype('int16').tobytes()

				# print('len(newI)={}'.format(len(newI)))
				# print('len(newQ)={}'.format(len(newQ)))

				newI=np.array(struct.unpack(fmt,newI))*(2*0.3838e-3)/(N_acq_single*2*8)
				newQ=np.array(struct.unpack(fmt,newQ))*(2*0.3838e-3)/(N_acq_single*2*8)
				# newI=np.array(struct.unpack(fmt,newI))/(N_acq_single*2)
				# newQ=np.array(struct.unpack(fmt,newQ))/(N_acq_single*2)
			  

				adcdataI[ch_vec[i]].append(newI)
				adcdataQ[ch_vec[i]].append(newQ)
			  

		return adcdataI,adcdataQ

	def get_readout_pulse_loop(self):
			'''
			This function uses loop over all the data array to read the dsp type and parameters
			If the regular fast decoding behaviour is weird check using this function
			Very long for high nb of measurements 
			'''
			self.reset_output_data()

			#for now we consider only the one same type of acq on all adc
			mode=self.acquisition_mode.get()

			length_vec,ch_vec=self.adc_events()

			N_adc_events=len(ch_vec)

			N_acq=np.sum(np.sum(length_vec))


			rep=[]
			count_meas=0

			empty_packet_count = 0

			if mode=='SUM':

				self.write("SEQ:START")
				time.sleep(0.1)

				while (count_meas//(16*N_adc_events))<self.nb_measure.get():

					r = self.ask('OUTPUT:DATA?')
					# print(r)

					if r == 'ERR':

						log.error('rfSoC: Instrument returned ERR!')

						break

					elif len(r)>1:

						empty_packet_count = 0

						# print(rep,r)
						print(datetime.datetime.now())
						rep = rep+r
						print(datetime.datetime.now(),'\n')
						#to modify manually depending on what we

						count_meas+=len(r)


					elif r==[3338]:

						empty_packet_count += 1
						time.sleep(0.1)

					if empty_packet_count>20:

						log.warning('Data curruption: rfSoC did not send all data points({}).'.format(count_meas//(16*N_adc_events)))

						break

						# if r==[3338] and count_meas == self.nb_measure.get():

						# count_meas = self.nb_measure.get()

			if mode=='RAW':

				self.write("SEQ:START")
				time.sleep(0.1)

				print(self.nb_measure.get())
				while count_meas<self.nb_measure.get():

					r = self.ask('OUTPUT:DATA?')

					if len(r)>1:
						print(len(r))
						rep = rep+r
						#to modify manually depending on what we
						#TODO : figure a way to do it auto depending on the adcs ons and their modes
						#now for 1 ADC in accum
						# count_meas+=len(r)//16
						count_meas+=len(r)//((8+N_acq))


					elif r==[3338]:

						count_meas=self.nb_measure.get()



			# while time.perf_counter()<(tstart+duree):

			#     time.sleep(tick)
			#     r = self.ask('OUTPUT:DATA?')
			#     if len(r)>1:
			#         rep = rep+r

			self.write("SEQ:STOP")
			# #we ask for last packet and add it
			# r = self.ask('OUTPUT:DATA?')
			# if len(r)>1:
			#         rep = rep+r

			# data decoding
			i=0
			TSMEM=0
			while (i + 8 )<= len(rep) : # at least one header left

				entete = np.array(rep[i:i+8])
				X =entete.astype('int16').tobytes()
				V = X[0]-1 # channel (1 to 8)
				DSPTYPE = X[1]
				#N does not have the same meaning depending on DSTYPE
				N = struct.unpack('I',X[2:6])[0]
				#number of acquisition points in continuous
				#depends on the point length
				NpCont = X[7]*256 + X[6]
				TS= struct.unpack('Q',X[8:16])[0]

				# print the header for each packet
				# print("Channel={}; N={}; DSP_type={}; TimeStamp={}; Np_Cont={}; Delta_TimeStamp={}".format(V,N,DSPTYPE,TS,NpCont,TS-TSMEM))

				TSMEM=TS

				iStart=i+8
				# if not in continuous acq mode
				if ((DSPTYPE &  0x2)!=2):
					# raw adcdata for each Np points block
					if ((DSPTYPE  &  0x1)==0):
						Np=N
						adcdataI[V]=np.concatenate((adcdataI[V], np.right_shift(rep[iStart:iStart+Np],4)*0.3838e-3))

					#in the accumulation mode, only 1 I and Q point even w mixer OFF
					#mixer ON or OFF
					if ((DSPTYPE  & 0x01)==0x1):
						Np=8
						D=np.array(rep[iStart:iStart+Np])
						X = D.astype('int16').tobytes()

						#I  dvided N and 2 bcse signed 63 bits aligned to the left
						# mod div by 4 to fix amplitude -Arpit, Martina
						I=  struct.unpack('q',X[0:8])[0]*(0.3838e-3)/(N*2*4)
						Q=  struct.unpack('q',X[8:16])[0]*(0.3838e-3)/(N*2*4)

						# print the point
						# print("I/Q:",I,Q,"Amplitude:",np.sqrt(I*I+Q*Q),"Phase:",180*np.arctan2(I,Q)/np.pi)

						adcdataI[V]=np.append(adcdataI[V], I)
						adcdataQ[V]=np.append(adcdataQ[V], Q)


				#in our case we dont need the continuous mode for now
				# continuoous acquisition mode with accumulation (reduce the flow of data)
				elif ((DSPTYPE &  0x3)==0x3):
					# mixer OFF : onlyI @2Gs/s or 250Ms/s
					if ((DSPTYPE  & 0x20)==0x0):
						# points are already averaged in the PS part
						# format : 16int
						Np = NpCont
						adcdataI[V]=np.concatenate((adcdataI[V], np.right_shift(rep[iStart:iStart+Np],4)*0.3838e-3))

					# mixer ON : I and Q present
					elif ((DSPTYPE  & 0x20)==0x20):
						Np = NpCont
						adcdataI[V]=np.concatenate((adcdataI[V],np.right_shift(rep[iStart:Np:2],4)*0.3838e-3))
						adcdataQ[V]=np.concatenate((adcdataQ[V], np.right_shift(rep[iStart+1:Np:2],4)*0.3838e-3))


				i = iStart+Np # index of the new data block, new header

			# print("********************************************************************")
			# print(len(rep),"Pts treated in ",time.perf_counter()-tstart,"seconds")
			# print("********************************************************************")

			#reshaping results

			if mode=='SUM':

				# print('*** ',length_vec)

				adcdataI=[np.array(adcdataI[v]).reshape(self.nb_measure.get(),len(length_vec[v])).T for v in range(8)]
				adcdataQ=[np.array(adcdataQ[v]).reshape(self.nb_measure.get(),len(length_vec[v])).T for v in range(8)]


			if mode=='RAW':

				adcdataI=[np.array(adcdataI[v]).reshape(self.nb_measure.get(),np.sum(length_vec[v],dtype=int)) for v in range(8)]

				# adcdataI=[np.array(adcdataI[v]).reshape(self.nb_measure.get(),np.sum(np.sum(ch[v],dtype=int))) for v in range(8)]
				adcdataI=[np.mean(adcdataI[v],axis=0) for v in range(8)]

				adcdataI=np.array([np.split(adcdataI[v],[sum(length_vec[v][0:i+1]) for i in range(len(length_vec[v]))]) for v in range(8)])

			return adcdataI,adcdataQ




	# def get_single_readout_pulse(self):

	#     self.reset_output_data()

		# print(self.ADC_events.get())

	#     if len(self.ADC_events.get())>1:

	#         raise ValueError('Need only one readout pulse in the sequence for this function')

	#     else :

	#         readout=self.ADC_events.get()[0]

	#     #pick up the parameters of the wanted ADC
	#     ch=readout.channel
	#     ch_obj=getattr(self,'ADC'+ch[2])

	#     fmix=ch_obj.fmixer.get()
	#     decfactor=ch_obj.decfact.get()
	#     mode=self.acquisition_mode.get()

	#     N_acq=int((readout.t_duration)/0.5e-9)
	#     #Ethernet data transfer
	#     t_wait=(N_acq)*16.e-9
	#     N_wait=int((t_wait)/0.5e-9)

	#     # 8 I and Q channels
	#     adcdataI = [[],[],[],[],[],[],[],[]]
	#     adcdataQ = [[],[],[],[],[],[],[],[]]


	#     tick = 0.1
	#     duree = 2

		# print('mode is {}'.format(mode))
	#     count_meas=0
		# print('count_meas={}'.format(count_meas))
	#     rep=[]

	#     if mode=='SUM':

	#         self.write("SEQ:START")
	#         time.sleep(0.1)

	#         while count_meas is not 1:

	#             r = self.ask('OUTPUT:DATA?')

	#             if len(r)>1:
	#                 rep = rep+r
	#                 #to modify manually depending on what we
	#                 #TODO : figure a way to do it auto depending on the adcs ons and their modes
	#                 #now for 1 ADC in accum

	#             elif r==[3338]:

	#                 count_meas=1

	#     if mode=='RAW':

	#         self.write("SEQ:START")
	#         time.sleep(0.1)


	#         while count_meas is not 1:

	#             r = self.ask('OUTPUT:DATA?')

	#             if len(r)>1:
					# print(len(r))
	#                 rep = rep+r
	#                 #to modify manually depending on what we
	#                 #TODO : figure a way to do it auto depending on the adcs ons and their modes
	#                 #now for 1 ADC in accum

	#             elif r==[3338]:
	#                 count_meas=1



	#     # while time.perf_counter()<(tstart+duree):

	#     #     time.sleep(tick)
	#     #     r = self.ask('OUTPUT:DATA?')
	#     #     if len(r)>1:
	#     #         rep = rep+r

	#     self.write("SEQ:STOP")
	#     #we ask for last packet and add it
	#     r = self.ask('OUTPUT:DATA?')
	#     if len(r)>1:
	#             rep = rep+r

	#     # data decoding
	#     tstart = time.perf_counter()
	#     i=0
	#     TSMEM=0
	#     while (i + 8 )<= len(rep) : # at least one header left

	#         entete = np.array(rep[i:i+8])
	#         X =entete.astype('int16').tobytes()
	#         V = X[0]-1 # channel (1 to 8)
	#         DSPTYPE = X[1]
	#         #N does not have the same meaning depending on DSTYPE
	#         N = struct.unpack('I',X[2:6])[0]
	#         #number of acquisition points in continuous
	#         #depends on the point length
	#         NpCont = X[7]*256 + X[6]
	#         TS= struct.unpack('Q',X[8:16])[0]

			# print the header for each packet
			# print("Channel={}; N={}; DSP_type={}; TimeStamp={}; Np_Cont={}; Delta_TimeStamp={}".format(V,N,DSPTYPE,TS,NpCont,TS-TSMEM))

	#         TSMEM=TS

	#         iStart=i+8
	#         # if not in continuous acq mode
	#         if ((DSPTYPE &  0x2)!=2):
	#             # raw adcdata for each Np points block
	#             if ((DSPTYPE  &  0x1)==0):
	#                 Np=N
	#                 adcdataI[V]=np.concatenate((adcdataI[V], np.right_shift(rep[iStart:iStart+Np],4)*0.3838e-3))

	#             #in the accumulation mode, only 1 I and Q point even w mixer OFF
	#             #mixer ON or OFF
	#             if ((DSPTYPE  & 0x01)==0x1):
	#                 Np=8
	#                 D=np.array(rep[iStart:iStart+Np])
	#                 X = D.astype('int16').tobytes()

	#                 #I  dvided N and 2 bcse signed 63 bits aligned to the left
	#                 I=  struct.unpack('q',X[0:8])[0]*(0.3838e-3)/(N*2)
	#                 Q=  struct.unpack('q',X[8:16])[0]*(0.3838e-3)/(N*2)

					#print the point
					# print("I/Q:",I,Q,"Amplitude:",np.sqrt(I*I+Q*Q),"Phase:",180*np.arctan2(I,Q)/np.pi)

	#                 adcdataI[V]=np.append(adcdataI[V], I)
	#                 adcdataQ[V]=np.append(adcdataQ[V], Q)

	#         # continuoous acquisition mode with accumulation (reduce the flow of data)
	#         elif ((DSPTYPE &  0x3)==0x3):
	#             # mixer OFF : onlyI @2Gs/s or 250Ms/s
	#             if ((DSPTYPE  & 0x20)==0x0):
	#                 # points are already averaged in the PS part
	#                 # format : 16int
	#                 Np = NpCont
	#                 adcdataI[V]=np.concatenate((adcdataI[V], np.right_shift(rep[iStart:iStart+Np],4)*0.3838e-3))

	#             # mixer ON : I and Q present
	#             elif ((DSPTYPE  & 0x20)==0x20):
	#                 Np = NpCont
	#                 adcdataI[V]=np.concatenate((adcdataI[V],np.right_shift(rep[iStart:Np:2],4)*0.3838e-3))
	#                 adcdataQ[V]=np.concatenate((adcdataQ[V], np.right_shift(rep[iStart+1:Np:2],4)*0.3838e-3))


	#         i = iStart+Np # index of the new data block, new header

		# print("********************************************************************")
		# print(len(rep),"Pts treated in ",time.perf_counter()-tstart,"seconds")
		# print("********************************************************************")


	#     return adcdataI,adcdataQ
