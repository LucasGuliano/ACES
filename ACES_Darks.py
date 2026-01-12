#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 10 14:39:12 2025

@author: lguliano
"""
from ACES_Camera_Data import ACES_Camera_Data

import numpy as np
import os

def ACES_Dark(data, exp_time, gang_num):
   
    #Location of dark data, should be a singl SEQ file of the correct exposure time
    dark_base = '/Users/lguliano/ACES/Data/DARKS/'
    dark_dir = dark_base + str(exp_time)+'/'
    
    #If the direcotry exists for that exposure time
    if os.path.isdir(dark_dir) == True:
        
        #Set the name of the saved dark file as an npy file
        dark_npy = dark_dir+'ACES_Darks_'+str(exp_time)+'.npy'
        
        #First check if there is a dark already made and saved as a npy file
        if os.path.isfile(dark_npy) == False:
            #If not, create a median dark file from the dataset
            print()
            print('No dark file found for this exposure time...')
            print('Creating median dark for exposure time: '+str(exp_time))
            print()
            dark_data, dark_meta = ACES_Camera_Data(dark_dir, gang_num, frametype='Dark')
            dark_frame = np.median(dark_data, axis=0).astype(int)
            
            #Save to dark file
            print()
            print('Saving dark file to: '+dark_npy)
            np.save(dark_npy, dark_frame)
        
        #If an npy file is there, use it to perform dark subtraction
        if os.path.isfile(dark_npy) == True:
            print()
            print('Loading dark frame: '+dark_npy)
            dark_frame= np.load(dark_npy)
            print()
            print('Subtracting dark frame from data')
            for d in range(0,len(data)):
                data[d,:,:] =  data[d,:,:] - dark_frame
    
    #If there is no directory for dark data, exit and inform the user
    else:
        print('Dark data does not exist for that exposure time')
        print('Please verifiy there is dark data at....')
        print(dark_dir)
        print('Data returned without dark subtraction')
        
    return data