#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  8 11:06:14 2025

@author: lguliano
"""
import matplotlib.pyplot as plt
import numpy as np

def ACES_Image_Plotter(data, frame_num):
    plt.imshow(data[frame_num,:,:])
    plt.title('Frame number: '+str(frame_num))

def ACES_Middle_Image_Plotter(data):
    mid = len(data) // 2
    plt.imshow(data[mid,:,:])
    plt.title('Middle frame of dataset')

def ACES_Pixel_Plotter(data, pixel):
    frame_num = [i for i in range(0, len(data))]
    plt.plot(data[:,pixel[0],pixel[1]])
    plt.scatter(frame_num, data[:,pixel[0],pixel[1]], color='red')
    plt.xlabel('Frame Number')
    plt.ylabel('Intensity')
    plt.title('Pixel Intentensity for: '+str(pixel))
    
def ACES_Intensity_Plotter(x, intensity):
    plt.plot(x, intensity)
    plt.scatter(x, intensity, color='red')
    plt.ylabel('Intensity')
    plt.title('Pixel Intentensity')

def ACES_Multi_Frame_Image(data, n_display):
    
    total_files = len(data)
    n_files = total_files // n_display
    
    imgs = []
    
    for f in range(0,n_display):
        imgs.append(data[n_files*f,:,:])
        
    ax = n_display
    ay = 1
    fig =plt.figure()
    for i in range(0,n_display):
        sub = fig.add_subplot(ax,ay,i+1)
        sub.axis('off')
        sub.imshow(imgs[i])
    plt.show()    

def ACES_Scan_Plotter(meta, scan_list):
    
    #array of the camera positional and position values
    cam_pos = []
    cam_count = []
    for m in meta:
        cam_pos.append(m.pos)
        cam_count.append(m.frameCounter)
        
    #plot full dataset
    plt.plot(cam_count, cam_pos)
    plt.xlabel('Frame Count')
    plt.ylabel('Position (mm)')
    plt.title('Selected Scans')
    
    #Overplot individual scans
    for scan in scan_list:
        plt.plot(cam_count[scan[0]:scan[1]], cam_pos[scan[0]:scan[1]])
        
def ACES_Sample_Plotter(OPD, OPD_intrp, real_data, data_intrp, pixel):
    plt.plot(OPD[:,pixel[0],pixel[1]], real_data[:,pixel[0],pixel[1]], color='blue')
    plt.scatter(OPD[:,pixel[0],pixel[1]], real_data[:,pixel[0],pixel[1]], color='blue')
    plt.scatter(OPD_intrp[:,pixel[0],pixel[1]], data_intrp[:,pixel[0],pixel[1]], color='red', marker='*')
    plt.ylabel('Intensity')
    plt.xlabel('Position (mm)')
    plt.title('Interpolated (*) vs. Real Data (o)')
    

def ACES_FT_Plotter(ft, freq):
    
    plt.plot(freq,np.abs(ft))
     
    plt.xlabel('Wavenumber (cm^-1)')
    plt.ylabel('Intensity')
    plt.title('Fourier Transform Plot')

def ACES_ZPD_Plotter(pos, data):
    #EACH PIXEL NEEDS ITS OWN ZPD, HOW TO HANDLE THAT?
    x_axis = np.shape(data)[2]
    y_axis = np.shape(data)[1]
    
    test_list = []
    test_list_2 = []
    test_list_3 = []

    for x in range(0, x_axis):
        test_list_3.append(pos[np.where(data[:,6,x] == max(data[:,6,x]))[0][0]])
        test_list_2.append(pos[np.where(data[:,4,x] == max(data[:,4,x]))[0][0]])
        test_list.append(pos[np.where(data[:,2,x] == max(data[:,2,x]))[0][0]])
    
    plt.plot(test_list)
    plt.plot(test_list_2)
    plt.plot(test_list_3)  
    plt.ylabel('ZPD location (mm)')
    plt.xlabel('Pixel X value')
    plt.title('ZPD for each Pixel')
    
def ACES_SNR_Plotter(SNR, freq):
    plt.plot(freq, SNR)
    plt.ylabel('SNR')
    plt.xlabel('Wavenumber (cm^-1)')
    plt.title('Signal to Noise Ratio')
    