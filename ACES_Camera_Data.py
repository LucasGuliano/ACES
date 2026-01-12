#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  4 14:40:35 2025

@author: lguliano
"""

from ReadSeqMod_Ganged import ReadSeq 

import os
import numpy as np
import pandas as pd

import time
import h5py


# time_stamper function used to assign a time to each subframe from the full frame data
# Takes the start and end time of series of frames and assigns a time to each subframe
# Needs to be done over full sequence files due to accuracy limitations on frame timestamps
# Multiple frames will have the same timestamp, so can't get subframe from just timestamps, need full series

def time_stamper(meta, num_frames, gang_num):
    
    meta_stamped = meta
    
    time_frame = meta_stamped[-1].timestamp - meta_stamped[0].timestamp
    
    seconds_2_nano = time_frame.seconds * 1e9
    micro_2_nano = time_frame.microseconds * 1e3
    nanoseconds = seconds_2_nano + micro_2_nano
    
    #Get the step for each subframe, assuming that the time starts at the first full frame end
    ns_per_frame = nanoseconds / (len(meta_stamped)-(gang_num-1))
    ns = pd.Timedelta(str(ns_per_frame)+' ns')
    
    #Convert to Panda time objects for greater precision:
    pandatime = []
    for m in meta_stamped:
        pandatime.append(pd.Timestamp(m.timestamp))
    
    #Frame number to base time off of, should be the last subframe of the first full frame
    base_fn = gang_num - 1
        
    #Starting at the second full frame, assign each subframe a time based on the step size
    for p in range(0,len(meta_stamped)):
        temptime = pandatime[base_fn] + (ns*(p-base_fn))
        
        #For datetime object
        meta_stamped[p].timestamp = temptime.to_pydatetime()
        
        #For Pandas time object
        #meta_stamped[p].timestamp = temptime
        
    return meta_stamped

#Reindex frames to ensure that it starts at zero and counts up
def frame_count_fixer(meta):
    
    meta_framed = meta
    
    #Check to see if there is a zero frame
    good_reset = False
    for m in meta:
        if m.frameCounter == 0:
            good_reset = True
            break
    
    #if there is not a zero index, just return the data
    if good_reset == False:
        print('This data did not have a frame reset')
        print('THERE MAY BE ERRORS ALIGNING THIS DATA WITH THE LOGS')
        return meta_framed
    
    #If it does have a good reset, check to see if it needs to be reindexed
    if good_reset == True:    
        #If frame 0 starts at zero, no need to correct
        if meta[0].frameCounter == 0:
            print("No need to reindex")
            return meta_framed
        
        #If it is not zero, then find how many files need to be shifted    
        else:
            print('Reindexing meta data')
            index_shift = 0
            keep_counting = True
            #Loop and count until it finds the frame that starts at zero
            while keep_counting == True:
                if meta[index_shift].frameCounter == 0:
                    keep_counting = False
                else:
                    index_shift = index_shift + 1
                    
            #Print out the frame where the reset happened   
            print()
            print('Frame counter reset found on frame number: ',index_shift)
            print()
            
            #Print warning if reset occurs late in dataset
            if index_shift >100:
                print('########################')
                print('WARNING!!!!!!!')
                print('Frame reset occurs late in this dataset')
                print('You should investigate and make sure files are correct')
                print('########################')
            #Reindex the first frames to start at zero
            for i in range(0,index_shift):
                meta[i].frameCounter = i
                
            #Reindex the rest of the frames
            for i in range(index_shift,len(meta)):
                meta[i].frameCounter = meta[i].frameCounter + index_shift
            
            #Return the reindexed meta
            return meta_framed


def ACES_Camera_Data(camera_dir, gang_num=1, frametype='normal'):
    ############################
 
    image_dir = os.path.join(os.path.expanduser('~'), 'ACES', camera_dir)
    seq_list = os.listdir(image_dir)
    
    #Only look at files that are seq files
    for seq in seq_list:
        if seq[-3:] != 'seq':
            seq_list.remove(seq)
    
    #Sort in order of file name (time)
    seq_list.sort()
    
    #################################
    num_seqs = len(seq_list)
    print('Reading from the following '+str(num_seqs)+' seq files...')
    print()
    print(seq_list)

    #Build empty list to store data and meta of each file
    data_list = []
    meta_list = []
    
    seq_count = 0
    for seqs in seq_list:
        
        #Time each loop
        start_time = time.perf_counter()
        
        #Increase seq count by one to report the number of the file being read
        seq_count = seq_count + 1
        
        #Get the specifc file
        seqfile = image_dir+seqs
        
        #Print which seq file is being analyzed
        print()
        print()
        print('Reading seq file: '+seqs)
        print('File number '+str(seq_count)+'/'+str(num_seqs))
    
        #Read in the data
        new_data,new_meta,new_seq = ReadSeq(seqfile, gang_num=gang_num)
        
        #Get data sizes
        num_frames = np.shape(new_data)[0]
        #num_rows = np.shape(new_data)[1]
        #num_columns = np.shape(new_data)[2]
        
        # For each seq file, get a UTC time stamp for each subframe
        new_meta = time_stamper(new_meta, num_frames, gang_num)
        
        read_end = time.perf_counter()
        read_time = read_end - start_time
        print(f"Reading data took:  {read_time:.4f} seconds")
        
        data_list.append(new_data)
        meta_list.append(new_meta)
    
    #With each file read, must be merged together, tricky for large datasets
    concat_start = time.perf_counter()
    
    #Now there is a list of arrays containing the data from each seq file
    #Utilize h5py to merge all of these and not overwhelm everything
    temp_h5py = camera_dir+'/temp_data.h5'
    
    #Get the shape of the dataset
    X = np.shape(data_list[0])[2]
    Y = np.shape(data_list[0])[1]
    
    print()
    print()
    print('Merging data and meta lists from each sequence file together...')
    print()

    # Open an HDF5 file in write mode
    with h5py.File(temp_h5py, 'w') as f:

        #Create array to hold all of the image data
        image_set = f.create_dataset('image_data', shape=(0, Y, X), maxshape=(None, Y, X), dtype=int)
        # Append each array to the dataset
        for arr in data_list:
            # Resize the dataset
            image_set.resize(image_set.shape[0] + arr.shape[0], axis=0) 
            # Write the array to the allocated space
            image_set[-arr.shape[0]:] = arr 
    
    #Read into numpy array
    with h5py.File(temp_h5py, 'r') as f:
        h5py_im_data = f['image_data']

        # Create an empty NumPy array of the desired shape and dtype
        data = np.empty(h5py_im_data.shape, dtype=h5py_im_data.dtype)

        # Read the data directly into the NumPy array
        h5py_im_data.read_direct(data)
    
    #Delete large temporary file
    os.remove(temp_h5py)
    
    
    #Meta is easier, just concate directly to numpy
    meta = np.concatenate(meta_list)
    
    #Time report
    concat_end = time.perf_counter()
    concat_time = concat_end - concat_start
    print(f"Concat took:  {concat_time:.4f} seconds")
    
    
    #reindex the data to ensure it starts at zero frame count, need to do on the full data set
    #Don't perform for darks to avoid incorrect error messages on frame counter
    if frametype == 'normal':
        meta = frame_count_fixer(meta)

    
    
    return data, meta


