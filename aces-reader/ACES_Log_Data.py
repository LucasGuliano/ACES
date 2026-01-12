#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  3 13:52:57 2025

@author: lguliano

"""

# Read in ACES log data


import os
import datetime as dt
from aces_reader.mimic_log_parser import parse_mimic_logs


def ACES_Log_Data(log_dir):

    # Set where the logs will be read from
    data_dir = os.path.join(os.path.expanduser('~'), 'ACES', log_dir)
    
    #Read in the data from the logs and grab the data frame
    log_dictionary = parse_mimic_logs(os.path.join(data_dir))
    log_df = log_dictionary['df']
    
    
    # FRAME DATA FIX (DELETE LATER, ONLY NEEDED DUE TO ERROR IN DATASET)
    #log_df['position_3'] = log_df['position_3'] / 3.9551e-5
    
    
    ### BUILD UTC TIME ARRAY
    for i in range(0,len(log_df)):
        temp_time = dt.datetime(1970,1,1) + dt.timedelta(seconds=log_df['time'][i])
        
        #Datetime Object
        log_df['utcTime'][i] = temp_time
    
        #Convert to pandas time object for better precision
        #log_df['utcTime'][i] = pd.Timestamp(temp_time)
        
    #####################
    #REMOVE THE USELESS ENTRIES
    ########################
    log_df=log_df.drop('time', axis=1)
    log_df=log_df.drop('step', axis=1)
    log_df=log_df.drop('overrun', axis=1)
    log_df=log_df.drop('set_point', axis=1)
    log_df=log_df.drop('position_1', axis=1)
    log_df=log_df.drop('position_2', axis=1)
    log_df=log_df.drop('controller_out', axis=1)
    log_df=log_df.drop('voltage', axis=1)
    log_df=log_df.drop('utcTimeInt', axis=1)
    log_df=log_df.drop('velocity', axis=1)
  

    return log_df

