#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 12 17:20:50 2025

@author: lguliano
"""

#Function to take in ACES log and meta image data and write a position to the metadata

#Also takes in a subset range of camera data to work on and a specific pixel to analyze

import numpy as np
import h5py
import pickle
import pandas as pd
import os
from scipy.fft import rfft, rfftfreq


##########################################################################
##########################################################################

#Function that adds interpolated position from log files into the camera meta objects
def Camera_Log_Interpolation(meta, logs, data):
    
    #Arrays to fill from camera meta data and log df object to feed into np.interp
    log_counts = []
    log_position = []
    
    camera_counts = []

    #Get array of log positions
    log_position_array = logs['position_0'].to_numpy()
    for p in log_position_array:
        log_position.append(p)
    
    
    ######################
    ### BY FRAME COUNTS ##
    ######################
    
    #Get array of log counts
    log_counts_array = logs['position_3'].to_numpy()
    for c in log_counts_array:
        log_counts.append(c)
     
    #Get an array of the frame counts from the camera data
    for c in meta:
        camera_counts.append(c.frameCounter)
        
    #Use interpolation to get camera positional values
    camera_position = np.interp(camera_counts, log_counts, log_position)
    
    #Append positional data to meta objects
    for i in range(0, len(meta)):
        #Camera positional data
        meta[i].pos = camera_position[i]
 
##########################################################################
##########################################################################

#Take only a subset of data, needed for faster processing
def Data_Subset(data, y_range, x_range):
    print('Data resized to: '+str(y_range[1] - y_range[0])+'x'+str(x_range[1] - x_range[0]))
    data = data[:,y_range[0]:y_range[1], x_range[0]:x_range[1]]
    return data

##########################################################################
##########################################################################

#Average a defined bin size of pixels and return the data
def Pixel_Averager(data, y_bin=1, x_bin=1, fullframe='n'):
    
    #If set to the full frame, bin the full frame
    if fullframe=='y':
        y_bin = np.shape(data)[0]
        x_bin = np.shape(data)[1]
    
    print('Creating averaged bins of data '+str(y_bin)+'x'+str(x_bin))
    #Get the shape of the binned data that will be returned, rounded to nearest whole number
    y_axis = int(np.shape(data)[1] / y_bin)
    x_axis = int(np.shape(data)[2] / x_bin)
    
    #number of frames
    frames = np.shape(data)[0]
    
    #Array of avearge data with the correct binned frames
    average_data = np.zeros([frames, y_axis, x_axis])
    
    for y in range(0,y_axis):
        print('Working on binned row: '+str(y))
        for x in range(0, x_axis):
            #Get the correct indices for the binned data
            y1 = y * y_bin
            y2 = y1 + y_bin
            x1 = x * x_bin
            x2 = x1 + x_bin
            
            print('Averaging pxiels: '+str(y1)+':'+str(y2)+','+str(x1)+':'+str(x2))
            
            #Get the data for the bin of pixels
            bin_data = data[:,y1:y2,x1:x2]
            
            #average over the y and  axis
            bin_average = np.average(bin_data, axis=(1,2))
            #Add to the averaged array
            average_data[:,y,x] = bin_average
    
    #return the avearged data
    return average_data

##########################################################################
##########################################################################

#Seperate data into single scans       
def Scan_Selector(meta, path_length):
    print("Selecting Scans")
    
    #List of index of each of the scans
    scan_list = []
    
    #array of the camera positional values
    cam_pos = []
    for m in meta:
        cam_pos.append(m.pos)
        
    #Convert to numpy array 
    cam_pos = np.array(cam_pos)
    
    #Set upper and lower bounds for determining scan
    upper = np.average(cam_pos) + path_length 
    lower = np.average(cam_pos) - path_length 
    
    #All data within the correct range
    good_data = np.where((cam_pos >= lower) & (cam_pos <= upper))[0]
    
    #Find places where the index jumps to get the bounds of each scan
    diff = np.diff(good_data)
    diff_index = np.where(diff !=1)[0]
    
    
    for i in range(0,len(diff_index)+1):
        
        #For the first scan, we want the first bit of good data, and the first place good data jumps (first diff index)
        if i == 0:
            new_indexes = [good_data[0],good_data[diff_index[0]]]
        
        #For the last scan, we want the position AFTER the last jump (diff_index[i-1] + 1) and the final piece of good data
        elif i == len(diff_index):
            new_indexes = [good_data[diff_index[i-1]+1], good_data[-1]]
        
        #For all other scans, we want to start right after the first diff jump (diff_index[i-1] + 1) and go to the next diff jump ((diff_index[i])
        else:
            new_indexes = [good_data[diff_index[i-1]+1], good_data[diff_index[i]]]
       
        #Append each scan
        scan_list.append(new_indexes)
        
    print('Data seperated into '+str(len(scan_list))+' scans')
    
    return scan_list
 
##########################################################################
##########################################################################
   
#Make arrays of the camera positions and real data 
def Positions_and_Real_Data(meta, real_data):
    
    #array of the camera positional values
    cam_pos = []
    for m in meta:
        cam_pos.append(m.pos)
        
    #Convert to numpy array 
    cam_pos = np.array(cam_pos)
    
    return cam_pos, real_data

##########################################################################
##########################################################################
#ZPD = Zero Path Difference
#OPD = Optical Path Difference

#Sort the camera position and real data by position, then evenly sample and return
def Sampler(pos, rd, sample_size, path_length, datatype):
    
    #Find direction of travel
    if pos[0] < pos[-1]:
        print('This is a forward moving scan')
        direction = 'positive'
    if pos[0] > pos[-1]:
        print('This is a backwards moving scan')
        direction = 'negative'
    
    #Get the data size
    x_axis = np.shape(rd)[2]
    y_axis = np.shape(rd)[1]
    
       
    ############################################################
    print('Generating an evenly spaced OPD list for each pixel')
    
    #Get the length of travel and determine how many samples will be used (same for all pixels)
    #Set it to some percentage less than 1 to avoid extra on edges due to non-symetric data
    #NOTE: This (*0.90) is set to use only 90% of the path to avoid data on either side if the scan didn't start near ZPD, since it needs to be even on each side for FT. 
    #NOTE: Adjust as needed based on the dataset, but try to start scans near ZPD if possible when taking data
    full_travel = 2 * path_length * 0.90 #Doubled to go from pos to OPD
    
    #Number of sampled data points to use, force all pixels to have the same number of samples for a scan
    num_samples = abs(full_travel // sample_size)
    
    #Force it to be an even number of samples
    if num_samples % 2 == 1:
        num_samples = num_samples + 1
        
    print('# of samples: '+str(num_samples))
    
    #Build arrays to store original OPD data and sampled OPD data FOR EACH PIXEL
    OPD = np.zeros([len(rd),y_axis, x_axis])
    OPD_sample = np.zeros([int(num_samples+1),y_axis, x_axis])
    
    #Done on a pixel by pixel basis
    for x in range(0, x_axis):
        for y in range(0, y_axis):
            #Get the ordered intensities of a single pixel
            pixel_data = rd[:,y,x]
            
            ################################
            #Find the brightest frame for that pixel and then call that corresponding position ZPD
            if datatype == 'white':
                zero_path = pos[np.where(pixel_data == max(pixel_data))[0][0]]
            
            if datatype == 'laser':
                zero_path = np.average(pos)
            #################################
    
            #Build the OPD list for that pixel with that value as the center
            OPD_pix_hold = []
            for p in pos:
                #OPD is the distance from ZPD * 2
                OPD_pix = (p - zero_path)*2
                OPD_pix_hold.append(OPD_pix)
            
            #Add list of OPD values for the given pixel
            OPD[:,y,x] = OPD_pix_hold
               
            #Make a list of evenly spaced positional values and interpolate their intensities
            OPD_temp_sample = []
            #Make sure that ZPD is included
            OPD_temp_sample.append(0)
             
            #Add an even amount of samples to both sides of ZPD
            for n in range(1,int(num_samples//2)+1):
                OPD_temp_sample.append((sample_size * n))
                OPD_temp_sample.append((sample_size * -n))
            
            #Sort the list
            OPD_temp_sample.sort()
            
            #If this scan is traveling backwards, reverse list to keep consistent
            if direction == 'negative':
                OPD_temp_sample.reverse()
            
            #Append to the main list for each pixel
            OPD_sample[:,y,x] = OPD_temp_sample
    
    ## Interpolate pixel data to sampled positions
    print('Interpolating pixel values to the evenly spaced OPD list')
    
    #Create array to hold the data with the same number of new frames as the sampled positions
    sample_data = np.zeros([len(OPD_sample),y_axis, x_axis])
    
    for x in range(0, x_axis):
        for y in range(0, y_axis):
            #For a given pixel, interpolate the intensity based of the sampled positions
            
            if direction == 'positive':
                pixel_sample = np.interp(OPD_sample[:,y,x], OPD[:,y,x], rd[:,y,x])
            #Numpy interp can only only INCREASING X values, so invert OPD and real data for interpolation
            if direction == 'negative':
                pixel_sample = np.interp(OPD_sample[:,y,x], OPD[:,y,x][::-1], rd[:,y,x][::-1])
            #Write interpolated data to sampled_data array
            sample_data[:,y,x] = pixel_sample
            
    print('Returning evenly spaced position and pixel data')
    print('')
    return OPD, OPD_sample, sample_data

##########################################################################
##########################################################################

def ACES_Interpolator(scan_list, positions, real_data, sample_size, path_length,datatype='white'):
    '''    
        OPD_list: An list of OPDs for each scan
                    OPD_list[x] will be the OPD values (centered at the brightest value as ZPD and double the measured values ) for a single scan
        
        OPD_sample_list: A list of the sampled OPD values
                    OPD_sample_list[x] will be the INTERPOLATED OPD values to be evenly spaced by sample size and centered at ZPD

        intrp_data_list: List of sampled and nterpolated datasets for each scan 
    '''
    # For each scan, transform positions and real_data into sample_pos and sample_data
    # Build of list of data for each scan and bundle into single array
    OPD_list = []
    OPD_intrp_list= []
    data_intrp_list = []

    #Loop for each scan
    for s in range(0, len(scan_list)):
        print('Performing interpolation on scan '+str(s+1)+'/'+str(len(scan_list)))
        
        #Function to interpolate data for each scan at the size of the set sample rate (set to white or laser)
        OPD, OPD_intrp, data_intrp = Sampler(positions[s], real_data[s], sample_size, path_length,datatype)
        
        #Build lists for each scan
        OPD_list.append(OPD)
        OPD_intrp_list.append(OPD_intrp)
        data_intrp_list.append(data_intrp)
        
    return OPD_list, OPD_intrp_list, data_intrp_list 

##########################################################################
##########################################################################

#Get the avearage METRIC value of a dataset
def Metric_Maker(sorted_data_list):
    #Lists to hold metic values
    max_intensity_list = []
    min_intensity_list = []
    average_intensity_list = []
    metric_list = []
    
    #Get the intensity values across all frames for each individual pixel
    for dataset in sorted_data_list:
        for y in range(0,np.shape(dataset)[1]):
            for x in range(0,np.shape(dataset)[2]):
                #Intensity value for each frame
                pixel_data = dataset[:,y,x]    
                # REPORT METRIC
                max_intensity = max(pixel_data)
                min_intensity = min(pixel_data)
                average_intensity = np.average(pixel_data)
                metric = (max_intensity - min_intensity) / average_intensity
                #Add to the list for each pixel
                max_intensity_list.append(max_intensity)
                min_intensity_list.append(min_intensity)
                average_intensity_list.append(average_intensity)
                metric_list.append(metric)
     
    #print out avearged metric across the dataset
    print('#####################')
    print('The max intensity is  : '+str(round(np.average(max_intensity_list),0)))
    print('The min intensity is  : '+str(round(np.average(min_intensity),0)))
    print('The avg intensity is  : '+str(round(np.average(average_intensity_list),0)))
    print('The ratio metric is   : '+str(round(np.average(metric_list),4)))
    print('#####################')

##########################################################################
##########################################################################

def ACES_Binned_Saver(data_sub, meta, logs, data_filename):
    
    #Filename to save the binned data subset as
    save_file_h5 = data_filename
    
    #Check to see if binned directory exists for dataset, if not create
    datadate = data_filename.split('/')[-1]
    binned_dir = data_filename.replace(datadate, '')
    if os.path.isdir(binned_dir) == False:
        print('Making directory: ',binned_dir)
        os.mkdir(binned_dir)
    
    #Save data to h5py for smaller file size and faster processing
    print('Saving datafile: ',save_file_h5)
    with h5py.File(save_file_h5, 'w') as f:
        f.create_dataset('data', data=data_sub)

##########################################################################
##########################################################################
 
def ACES_Restoration(base_dir):
    #Data directory (get from input)
    print('The following data directories are available: ')
    print()
    print(os.listdir(base_dir))
    print()
    data_dir = input(prompt='Which binned data subset should be restored?: ')
    full_data_dir = base_dir + data_dir + '/'
    
    #Check to make sure that exists, try again if it doesn't
    while os.path.isdir(full_data_dir) == False:
        print()
        print('That directory does not exist')
        print('Please select again from the following options: ')
        print()
        print(os.listdir(base_dir))
        print()
        data_dir = input(prompt='Which binned data subset should be restored?: ')
        full_data_dir = base_dir + data_dir + '/'
    
    #Binned data in Binned/ and log/meta info in Processed
    binned_dir = full_data_dir + 'Binned/'
    save_file_h5 = binned_dir + data_dir + '_binned_data.h5'
    
    processed_dir = full_data_dir + 'Processed/'
    save_file_pkl = processed_dir + data_dir + '_processed_meta_logs.pkl'
    
    #Restore binned data
    if os.path.isfile(save_file_h5):
        print()
        print('Restoring binned data subset')
        #Restore processed data from h5py object
        with h5py.File(save_file_h5, 'r') as f:
            data = np.array(f['data'])
    else:
        print('!!!!!!!!!!!')
        print('NO BINNED DATA EXISTS FOR THIS DATA SET!')
        print('!!!!!!!!!!!')
        
    #Restore meta data and logs
    if os.path.isfile(save_file_pkl):
        print()
        print('Restoring metadata and logs')
        with open(save_file_pkl, 'rb') as e:
            meta, logs = pickle.load(e)
    else:
        print('!!!!!!!!!!!')
        print('NO META OR LOG FILES ARE SAVED FOR THIS DATASET!')
        print('!!!!!!!!!!!')
        
    #Return subdata, meta, and logs
    return data, meta, logs, full_data_dir

##########################################################################
##########################################################################

#Perform a fourier transform of the data
def ACES_Transformer(scan_list, OPD_intrp_list, data_intrp_list, sample_size_cm):
    
    print()
    print("Generating Fourier Transforms of data")
    print()
    #OPD_sample will be the sampled positional values (OPDs) for a single pixel
    #samp_data will be to sampled intensity values for a given pixel
    #SHOULD BE THE SAME SIZE
    
    #Build a list of each scan to hold the FT arrays of size y by x
    ft_list = []
    freq_list = []
    
    #Loop over each scan
    for s in range(0, len(scan_list)):
        
        #Get the freqs for the scans (one freq list for each scan)
        freqs = rfftfreq(len(OPD_intrp_list[s]), sample_size_cm)
        freq_list.append(freqs)
        
        #Build a list of FT data to append
        fouriers = []
        
        #Get the camera data for the scan
        working_data = data_intrp_list[s]
        
        #Loop over y and then x, and perform an FT at each pixel locations, results in a shape of ft_list -> [scan, y, x, ft data]
        for y in range(0,np.shape(working_data)[1]):
            xs=[]
            for x in range(0,np.shape(working_data)[2]):
                ft = rfft(working_data[:,y,x])
                xs.append(ft)
            fouriers.append(xs)
        ft_list.append(fouriers)
        
    return ft_list, freq_list
    
##########################################################################
##########################################################################
    
def Wavelength_Range(signal, freq, u1, u2):
    
    #Only look at data from the correct wavelengths
    wn1 = 1/ (u1 * 1e-4) #convert from 1/micron to 1/cm
    wn2 = 1/ (u2 * 1e-4)
    
    #Get the ranges
    upper_lim = np.where(freq < wn1)[0][-1]
    lower_lim = np.where(freq > wn2)[0][0]  
    
    #Chop by wavelengths
    freq = freq[lower_lim:upper_lim]
    signal = signal[lower_lim:upper_lim]
    
    return signal, freq
    

##########################################################################
##########################################################################

def Signal_2_Noise(signal, freq, window_size):
        
    #Convert to Pandas to use rolling window
    signal = pd.DataFrame(np.abs(signal))
    
    #Get a rolling STD value
    rolling_std = signal.rolling(window=window_size).std()
    
    SNR = signal / rolling_std
    
    return SNR
    
    
    
    
    


