#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  5 14:57:07 2025

@author: lguliano
"""

##################
# Designed to start at origin, move forward, and then backwards
##################

import serial_util_v3 as serial_util
import time

###############################
#Set the distance to travel and speed (in motor units)
OPD = 2500
set_speed = 5
###############################

#print the conversion to usable mks units

#establish connection to serial port, default comm set in serial_util
motor_port = serial_util._create_serial_port()
#Test if connection was successful
port_connect = serial_util._check_connection(motor_port)

#Establish flag to oscillate back and forth
direction_flag = 0

#Begin if connection was successful
if port_connect==True:
    
    #Set the motor speed to the above input
    serial_util._set_speed(motor_port, speed=set_speed)
    
    #Move motor to origin, wait until it gets there
    serial_util._move_to_origin(motor_port)
    while serial_util._check_connection(motor_port) == False:
        print('Moving to origin')
    print('Reached orign')

    #Start with testing true to give the user the options
    testing = True

###########################################
#########    TESTING LOOP #################
###########################################

    while testing == True:     
        #Allow user to either perform a test run or start oscillation
        print("Peform test or start oscillation?")
        test_input = input('Enter t for a test run or anything else to start: ')

        if test_input == 't':
            testing = True
            print('Performing test run')
            #Forwards and wait until finished
            serial_util._set_position(motor_port, stage='X', dx=OPD/2)
            print('Moving Forward')
            while serial_util._check_connection(motor_port) == False:
                time.sleep(0.1)
                
            #Backwards and wait until finished
            serial_util._set_position(motor_port, stage='X', dx=-OPD)
            print('Moving Backwards')
            while serial_util._check_connection(motor_port) == False:
                time.sleep(0.1)
                
            #Return to origin
            serial_util._move_to_origin(motor_port)
            print('Returning to origin')
            while serial_util._check_connection(motor_port) == False:
                time.sleep(0.1)

###########################################
#########   MAIN OSCILLATION LOOP #########
###########################################

        #When testing not set, enter endless loop of back and forth   
        #Starts at origin, moves forward half the OPD, moves backwards full OPD, then forward full OPD....
        if test_input != 't':
            testing = False
            print('Starting oscillation')
            
        while testing == False:
            
            #First step move forward hald the OPD from origin
            if direction_flag == 0:
                serial_util._set_position(motor_port, stage='X', dx=+OPD/2)
                while serial_util._check_connection(motor_port) == False:
                    time.sleep(0.1)
            
            #Add to the direction flag to alternate the direction of movement
            direction_flag += 1
            
            # Move backwards if the flag is odd, should happen first after the first half step forward
            if direction_flag % 2 == 1:
                serial_util._set_position(motor_port, stage='X', dx=-OPD)
                while serial_util._check_connection(motor_port) == False:
                    time.sleep(0.1)

            # Move forwards if the flag is even
            if direction_flag % 2 == 0:
                serial_util._set_position(motor_port, stage='X', dx=+OPD)
                while serial_util._check_connection(motor_port) == False:
                    time.sleep(0.1)
                
#Throw error and exit if unsuccessful connection
else:
    print('UNABLE TO CONNECT TO PORT')
    exit