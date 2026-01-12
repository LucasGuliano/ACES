#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 11 14:32:37 2025

@author: lguliano
"""

'''

Code used to analyze ACES Data


'''

from ACES_Processor import ACES_Processor

from ACES_Visualizer import ACES_Image_Plotter
from ACES_Visualizer import ACES_Multi_Frame_Image
from ACES_Visualizer import ACES_Middle_Image_Plotter
from ACES_Visualizer import ACES_Scan_Plotter
from ACES_Visualizer import ACES_Sample_Plotter
from ACES_Visualizer import ACES_FT_Plotter
from ACES_Visualizer import ACES_SNR_Plotter

from ACES_ToolKit import Data_Subset
from ACES_ToolKit import Pixel_Averager
from ACES_ToolKit import Scan_Selector
from ACES_ToolKit import Positions_and_Real_Data
from ACES_ToolKit import ACES_Interpolator
from ACES_ToolKit import ACES_Transformer
from ACES_ToolKit import Wavelength_Range
from ACES_ToolKit import Signal_2_Noise
from ACES_ToolKit import ACES_Binned_Saver
from ACES_ToolKit import ACES_Restoration


import matplotlib.pyplot as plt
import numpy as np


###########################
# GET PROCESSED DATA
##########################

data, meta, logs, working_dir = ACES_Processor()

###########################
# IMAGE VIEWIER
##########################

#Make a plot of evenly distributed number of frames to see how light moves
ACES_Multi_Frame_Image(data, 50)

#Display the middle frame to find a good pixel
ACES_Middle_Image_Plotter(data)

#OR display a given frame
ACES_Image_Plotter(data, 100)

###########################
# DATA SUBSET
##########################

################
#Display images to zoom in and find ROI
fig, ax = plt.subplots()
ax.imshow(data[0,:,:])

#WITHOUT CLOSING PLOT, grab the zoomed in ROI values
xlim=ax.get_xlim()
ylim=ax.get_ylim()
x_range = [int(xlim[0])+1, int(xlim[1])+1]
y_range = [int(ylim[1])+1, int(ylim[0])+1]


plt.close()

################
#Display subframe image to make sure it looks good
data_sub = Data_Subset(data, y_range, x_range)
plt.imshow(data_sub[0,:,:])

#Show more of the images
ACES_Multi_Frame_Image(data_sub, 50)

###########################
# DATA BINNING
##########################

#Bin by a set amount
x_bin = 2
y_bin = 2
data_sub = Pixel_Averager(data_sub, y_bin, x_bin)


###
#Or full frame averaging (ONLY RUN TO BIN ENTIRE FRAMES, SKIP OTHERWISE)
data_sub = Pixel_Averager(data_sub, fullframe='y')
####


#TAKES AWHILE SO MAY WANT TO SAVE AFTER
data_date = working_dir.split('/')[-2]
data_filename = working_dir + 'Binned/'+data_date+'_binned_data.h5'


###########################
#SAVE DATA
ACES_Binned_Saver(data_sub, meta, logs, data_filename)

###########################

#######################################################
################### RESTORE SUBSET  ###################
#######################################################

#SKIP AND RESTORE DATA (Restore binned subset data and all meta/log files)
data_sub, meta,logs, working_dir = ACES_Restoration('/Users/lguliano/ACES/Data/')

#######################################################


#####################################
# SCAN SELECTOR
#####################################
path_length = 25 #Full path length of travel from center in mm

scan_list = Scan_Selector(meta, path_length/2)

#Scan Plotter
ACES_Scan_Plotter(meta, scan_list)


#IF NEED TO REMOVE FIRST OR LAST NOT-FULL LAST SCAN
scan_list = scan_list[0:-1]


#####################################
# REAL POSITION AND INTENSITY DATA
#####################################

'''    
    positions: An array of the sequential camera positions for each scan 
                positions[x] will be a sequential list of the positions of scan number x with however many entries in that scan
    
    real_data: The real pixel intensity values (not interpolated) of each scan
                real_data[x] will be the images for a single scan with shape (frame_number, x, y)           
'''

positions = []
real_data = []

for scan in scan_list:
    pos, rd = Positions_and_Real_Data(meta[scan[0]:scan[1]], data_sub[scan[0]:scan[1], :, :])
    positions.append(pos)
    real_data.append(rd)


'''    
#####################################  
#Plot the same pixel for each scan
for i in range(0,len(positions)):
    plt.plot(positions[i],real_data[i][:,0,0])
    
for scan_num in range(0, len(scan_list)):
    plt.plot(positions[scan_num], real_data[scan_num][:,0,0])
    
    
#Plot a row in a single scan
for y in range(0, np.shape(real_data[0])[1]):
    plt.plot(positions[0],real_data[0][:,y,0])
    
'''

#####################################
# EVENLY SAMPLED AND INTERPOLATED DATA
#####################################


#Sample size for intepolation of data
sample_size = 632.816e-6 / 3 #HeNe laser in mm
sample_size_cm = sample_size / 10

OPD_list, OPD_intrp_list, data_intrp_list = \
    ACES_Interpolator(scan_list, positions, real_data, sample_size, path_length, datatype='white')

    
#Show the result of the interpolation
pixel = [0, 0]
scan_num = 1

ACES_Sample_Plotter(OPD_list[scan_num], OPD_intrp_list[scan_num], real_data[scan_num], data_intrp_list[scan_num], pixel)


'''
#Plot scans on top of eachother
for scan_num in range(0, 2):
    ACES_Sample_Plotter(OPD_list[scan_num], OPD_intrp_list[scan_num], real_data[scan_num], data_intrp_list[scan_num], pixel)

#Plot scans in one motor direction
for scan_num in range(0, len(scan_list)):
    if scan_num % 2 == 0:
        print('Plotting scan:',str(scan_num))
        ACES_Sample_Plotter(OPD_list[scan_num], OPD_intrp_list[scan_num], real_data[scan_num], data_intrp_list[scan_num], pixel)

'''

#####################################
# METRIC
#####################################
#Make the metric for all pxels
#Metric_Maker(sorted_data_list)



#####################################
# FOURIER TRANSFORMS
#####################################

# Shape of ft_list -> [scan, y, x, and the data]
# Shape of freq_list -> one freq list per scan

ft_list, freq_list = ACES_Transformer(scan_list, OPD_intrp_list, data_intrp_list, sample_size_cm)


#Set the wavelength range to look at (in microns)
u1 = 1.0 #micron
u2 = 1.7 #microns

########################
# PLOT THE FT DATA
######################
       
# Grab a dataset (ft list shape [scan number][y pixel[x pixel]])
ft = ft_list[1][0][0]
freq = freq_list[scan_num]

#Only use wavelength rangge
ft, freq = Wavelength_Range(ft, freq, u1, u2)

#Plot
ACES_FT_Plotter(ft, freq)

'''
############     Single Scans and (averaged) pixels   ############
for scan in range(0,len(scan_list)):
    ft = ft_list[scan][0][0]
    freq = freq_list[scan]
    ft, freq = Wavelength_Range(ft, freq, u1, u2)
    ACES_FT_Plotter(ft, freq)
    
    
for scan in range(0,len(scan_list)):
    if scan % 2 == 0:
        ft = ft_list[scan][0][0]
        freq = freq_list[scan]
        ft, freq = Wavelength_Range(ft, freq, u1, u2)
        ACES_FT_Plotter(ft, freq)
    
    

for scan in range(0,15):
    for x in range(0,2):
        for y in range(0,2):
            ft = ft_list[scan][x][y]
            freq = freq_list[scan]
            ft, freq = Wavelength_Range(ft, freq, u1, u2)
            ACES_FT_Plotter(ft, freq)
            
'''

#SNR
SNR = Signal_2_Noise(ft, freq, 1000)
ACES_SNR_Plotter(SNR, freq)


###################################################################
#Try averaging just the magnitude


###################  Average of scans and all pixels   ########################

#Get frequencies from first scan
freq = freq_list[0]

#Super average of all pixels (AVERAGING THE FT VALUES)
ft_average = np.mean(ft_list, axis=(0,1,2))

#Only use wavelength rangge
ft_average, freq = Wavelength_Range(ft_average, freq, u1, u2)

#Plot
ACES_FT_Plotter(ft_average, freq)

#SNR
SNR_avg = Signal_2_Noise(ft_average, freq, 1000)
ACES_SNR_Plotter(SNR_avg, freq)

plt.savefig('ACES_FT_spectrum_plot.png') 


###################  Average one pixel in all scans  ########################
#Get frequencies from first scan

###################  Average all pixels in a scan  ########################


# SAVE FT FILES




