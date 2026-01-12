#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 14 11:32:55 2025

@author: lguliano

Transforms ACES seq and log files into processed numpy arrays and dataframes

Processing involves:
    Reading in seq files, merging data into a singel numpy array
    Dark subtracting the dataset
    Interpolating positions of each frame using the log files

Processed data is then saved as a h5py file (data) and a pickle file (meta and logs)
h5py is better at saving large arrays quickly, but doesn't handle other objects well
pickle is an easy way to handle objects (like a dataframe or our meta objects), but slow to save large numpy arrays

Quick restoration of processed data also happens here with the option to reprocess if needed

User will end up with:
    data: numpy array of each camera frame, dark subtracted and frame count aligned
    logs: DataFrame of all logs with utcTime, position_0 (position), position_3 (frame number)
    meta: array of meta objects containing header info for each frame, including the interpoalted positional values
"""


import os
import shutil
import h5py
import pickle
import numpy as np

from ACES_Camera_Data import ACES_Camera_Data
from ACES_Log_Data import ACES_Log_Data
from ACES_Darks import ACES_Dark

from ACES_ToolKit import Camera_Log_Interpolation

def ACES_Processor():
 
#################################################################
    ############## PARAMETER SETUP #################
    #Number of subframes per main frame (ganged frames)
    gang_num = 4

    #Main data directory
    base_dir = '/Users/lguliano/ACES/Data/'
    
#################################################################
    
    ############### DIRECTORY SELECTION ################
    #Data directory (get from input)
    print('The following data directories are available: ')
    print()
    print(os.listdir(base_dir))
    print()
    data_dir = input(prompt='Which dataset should be processed?: ')
    full_data_dir = base_dir + data_dir + '/'
    
    #Check to make sure that exists, try again if it doesn't
    while os.path.isdir(full_data_dir) == False:
        print()
        print('That directory does not exist')
        print('Please select again from the following options: ')
        print()
        print(os.listdir(base_dir))
        print()
        data_dir = input(prompt='Which dataset should be processed?: ')
        full_data_dir = base_dir + data_dir + '/'
        
    #subdirectories
    camera_dir = full_data_dir + 'Camera/'
    log_dir = full_data_dir + 'Logs/'
    processed_dir = full_data_dir + 'Processed/'

    
    ################# DETEREMINE WHAT TO DO WITH DATA ##############
    #If processed directory exists
    if os.path.isdir(processed_dir):
        #And it is not empty
        if len(os.listdir(processed_dir)) != 0:
            print('Processed data already exists for this data set')
            print()
            data_option = input(prompt='Would you like to Restore (r) or Overwrite (o) this data?: ')
            
            while data_option not in ['r', 'o']:
                print()
                print('Invalid choice')
                data_option = input(prompt='Would you like to Restore (r) or Overwrite (o) this data?: ')
                
            #Verify before overwriting data
            if data_option ==  'o':
                verify = 'no'
                while verify != 'yes':
                    print('Are you sure you want to overwrite this data?!')
                    verify = input('Type `yes` if you are sure you want to overwrite this data (ctrl-c to exit): ')
       
        #If processed data directory exists but is empty
        else:
            print('Removing EMPTY processed data directory')
            shutil.rmtree(processed_dir) 
            #Treat it as new data to process
            data_option = 'n'
   
    #If no processed directory exists yet 
    else:
        #Set data option to New (n) to process new dataset
        print('No processed data exists for this dataset')
        data_option = 'n'
 
        
    ################# PROCESS NEW DATA ##############        
    if data_option == 'n' or data_option == 'o':
        
        ############ READ IN THE LOG DATA #########################
        print('READING DATA LOGS')
        logs = ACES_Log_Data(log_dir)
    
        #If overwriting data, first delete exist processed data
        if data_option == 'o':
            print('Removing processed data')
            shutil.rmtree(processed_dir)
        
        #Create new directory for processed data
        print('Creating directory',processed_dir)
        os.mkdir(processed_dir)
        
        #Read camera data and meta data
        data, meta = ACES_Camera_Data(camera_dir, gang_num)
        
        # Dark subtraction
        exp_time = round(meta[0].intTime * 1e3, 3)
        data = ACES_Dark(data, exp_time, gang_num)
        
        #Use interpolation of log data to assign positional value to each frame (meta object)
        print()
        print('Interpolating Camera and Log data to assign distance to each frame')
        Camera_Log_Interpolation(meta, logs, data)
        
        #Save data as H5Py Objects and Meta/Logs as Pickle Objects
        print()
        print('Saving processed data files....')
        save_file_h5 = processed_dir + data_dir + '_processed_data.h5'
        save_file_pkl = processed_dir + data_dir + '_processed_meta_logs.pkl'
        
        #Save data to h5py for smaller file size and faster processing
        with h5py.File(save_file_h5, 'w') as f:
            f.create_dataset('data', data=data)
        
        #Save logs and meta data to pickle object since it handles it better
        with open(save_file_pkl, 'wb') as e:  
            pickle.dump([meta, logs], e)
            
        print()
        print('New data files saved under',processed_dir)
 
    ################# RESTORE PROCESSED DATA ##############  
    if data_option == 'r':
        print('Restoring dataset')
        
        #Find saved data
        save_file_h5 = processed_dir + data_dir + '_processed_data.h5'
        save_file_pkl = processed_dir + data_dir + '_processed_meta_logs.pkl'
        
        #Restore processed data from h5py object
        with h5py.File(save_file_h5, 'r') as f:
            data = np.array(f['data'])
        
        # Restore the pickled meta and log data
        with open(save_file_pkl, 'rb') as e:
            meta, logs = pickle.load(e)

    #Return data, meta, and logs for analysis and the name of the working directory
    return data, meta, logs, full_data_dir


#########################################
#data, meta, logs = ACES_Processor()





















