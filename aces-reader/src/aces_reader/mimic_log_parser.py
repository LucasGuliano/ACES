import logging
import os
import struct

import numpy as np
import pandas as pd


def parse_mimic_logs(dir, logs_to_cat=np.inf, program_rate=2000, start_idx=0):
    concatenated_df = None
    info = {}
    logs_read = 0
    for (root, dirs, files) in os.walk(dir, topdown=True):
        for idx, file in enumerate(sorted(files)):
            if idx < start_idx:
                continue

            #if not file.startswith('mimic_'):
            if not file.startswith('modulator_'):
                logging.warning(f"Skipped spurious file named {file}")
                continue

            if logs_read > logs_to_cat:
                continue

            with open(os.path.join(dir, file), 'rb') as f:
                text = f.read()

            double_size = 8
            if idx == 0:
                doubles_in_first_row = 8
                # First row has some high-level info and not data
                # double fixed_vars[] = {(double) openLoop, (double) maxPosition, (double) sweepLength, (double) offset, Kp, Ki, Kd, tau};
                info = struct.unpack(">" + "d" * doubles_in_first_row, text[:doubles_in_first_row * double_size])
                # Skip the metadata row
                text = text[doubles_in_first_row * double_size:]

            doubles_per_row = 11
            rows = []
            for i in range(int(len(text) / (double_size * doubles_per_row))):
                row_idx = i * doubles_per_row * double_size
                if (row_idx + doubles_per_row) < len(text):
                    try:
                        doubles = struct.unpack(">" + "d" * doubles_per_row, text[row_idx:row_idx + doubles_per_row * double_size])
                        rows.append(doubles)
                    except struct.error:
                        print("Struct error!")
                        continue

            # double logVariables[] = {currentTime, utcTime, (double) step, (double) overruns, sp_filt, position[0], position[1], position[2], position[3], cmd[0], voltages[1]};
            columns = ['time', 'utcTime', 'step', 'overrun', 'set_point', 'position_0', 'position_1', 'position_2', 'position_3', 'controller_out', 'voltage']
            df = pd.DataFrame(rows, columns=columns)

            # Skip the dummy data
            if idx == len(files) - 1:
                logging.info("Cutting dummy data.")
                df = df.loc[df['step'] != -9999]

            logging.info(f"{file}: Start: {int(df['step'][0])}, End: {int(df['step'].iloc[-1])}")
            if concatenated_df is None:
                concatenated_df = df
            else:
                concatenated_df = pd.concat([concatenated_df, df], ignore_index=True)

            logs_read += 1

    # Interpolate the UTC times based on an assumed steady program rate.
    logging.info(f"Interpolating mimic UTC times based on a program rate of {program_rate} Hz.")
    start_step = concatenated_df.step[0]
    start_time = concatenated_df.utcTime[0]
    concatenated_df['utcTimeInt'] = concatenated_df.apply(
        lambda r: start_time + (r.step - start_step)*(1/program_rate),
        axis=1
    )

    logging.info("Calculating the instantaneous velocity across position_0.")
    sample_len = 1 / program_rate
    concatenated_df['velocity'] = np.gradient(concatenated_df['position_0'], sample_len)

    return {'df': concatenated_df, 'info': info}
