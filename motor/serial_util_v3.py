#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  5 14:57:50 2025

@author: lguliano
"""

#######################################################
# library of serial functions for optical linear stage
#######################################################

# from the pySerial library (may need to unistall serial and reinstall pySerial)
import serial

#create a serial port at specified name
def _create_serial_port(port_name = 'COM4', baudrate = 9600, timeout = 0.5):
    #note this obejct will automaticall open the port
    ser = serial.Serial(
    port = port_name,
    baudrate = baudrate,
    bytesize = serial.EIGHTBITS,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    xonxoff = False,
    timeout = timeout #will only collect data for this many seconds before returning
    )
    print(f'Opened serial port {ser.name}')
    return ser

#closes serial port
def _close_serial_port(ser):
    ser.close()
    print(f'Closed serial port {ser.name}')
    
#opens serial port
def _open_serial_port(ser):
    ser.open()
    print(f'Opened serial port {ser.name}')

#generic function that sends arbitrary command to serial port
def _serial_send_command(ser, command, bytes):
    assert(ser.isOpen())
    ser.write(command)
    return ser.read(bytes).decode('utf-8')

#checks if the connections to serial port is ok (returns true/false)
def _check_connection(ser, command = b'?R\r', bytes = 15):
    #print(repr(_serial_send_command(ser, command, bytes)))
    return _serial_send_command(ser, command, bytes) == '?R\rOK\n'

#moves the stage to the origin
def _move_to_origin(ser, stage = 'X', command = b'HY0\r', bytes = 15):
    command = f'H{stage}0\r'.encode()
    out = _serial_send_command(ser, command, bytes)
    # if out == 'HY0':
    #     print('Moved to origin')
    # else:
    #     print('Failed to execute command')

#gets the current position of the stage
def _get_position(ser, stage = 'X', command = b'?Y\r', bytes = 15):
    command = f'?{stage}\r'.encode()
    out = _serial_send_command(ser, command, bytes)
    return int(out[5:]) #ignore the Y+ in the beginning of the output

#gets the current speed setting of the stage
def _get_speed(ser, command=b'?V\r', bytes = 15): 
    out = _serial_send_command(ser, command, bytes)
    return int(out[4:]) #ignores the extra parts of the output

#sets a new speed setting of the stage
def _set_speed(ser, command=b'V0\r', speed=2, bytes = 15):
    command = f'V{speed}\r'.encode()
    out = _serial_send_command(ser, command, bytes)
    print('Speed set to: '+str(speed))
    return 

#sets the position based on current position
def _set_position(ser, stage = 'X', dx = 0, command = b'Y+0\r', bytes = 15):
    if dx >= 0:
        command = f'{stage}+{dx}\r'.encode()
    else:
        command = f'{stage}{str(dx)}\r'.encode()
    out = _serial_send_command(ser, command, bytes)
    #print(f'Moved the stage')