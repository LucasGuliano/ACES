import logging
import os
import struct
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from anglewrapper import wrap


def parse_stab_logs(dir, logs_to_cat=np.inf, program_rate=1000, start_idx=0):
    """
    stab_data = struct(
    single
    'ind',

    double
    'currentTime', 'winTime', 'GPSweek', 'GPSsec',

    singles
    'gyroX_raw', 'gyroY_raw', 'gyroZ_raw', 'gyroX', 'gyroY', 'gyroZ',
    'xBias', 'yBias', 'zBias',
    'xrateGV', 'yrateGV', 'zrateGV',
    'rate_delay', 'yaw', 'pitch', 'roll',
    'latitude', 'longitude', 'elevation',
    'sunAz', 'sunZen', 'sunAzEx', 'sunZenEx',
    'radius', 'psi', 'theta', 'psiCont', 'thetaCont', 'psiOff', 'thetaOff', 'psiInit', 'thetaInit',
    'xOff', 'yOff', 'imgX', 'imgY',
    'serialFlag', 'driftCor', 'state',
    'Ix', 'Iy', 'tau',
    'mirModel', 'fogExtrap', 'overruns',
    'headroom', 'seqNum', 'status', 'temp', 'check'
    # struct_fields = fieldnames(stab_data);
    # M = zeros(nlines, nvars);
    # for i = 1:length(filenames)
    # fid = fopen(fullfile(pathname, filenames
    # {i}), 'r', 'b');
    # for j = 1:nlines
    # M(j,:) = [fread(fid, 1, 'single');
    # fread(fid, 4, 'double');
    # fread(fid, nvars - 5, 'single')];
    # end
    # M(all(M == -9999, 2),:) = [];
    # fclose(fid);
    # for j = 1:length(struct_fields)
    # temp = getfield(stab_data, struct_fields
    # {j});
    # stab_data = setfield(stab_data, struct_fields
    # {j}, [temp;
    # M(:, j)]);
    # end
    # stab_data.imgX(stab_data.imgX == -999) = nan;
    # stab_data.imgY(stab_data.imgY == -999) = nan;
    """
    lines_per_file = 30000
    single_size = 4
    double_size = 8
    doubles_per_row = 4
    singles_per_row = 50
    bytes_per_row = (1 + singles_per_row) * single_size + 4 * double_size

    cols = [
        'ind',
        # Doubles
        'currentTime', 'winTime', 'GPSweek', 'GPSsec',
        # Singles
        'gyroX_raw', 'gyroY_raw', 'gyroZ_raw', 'gyroX', 'gyroY', 'gyroZ',
        'xBias', 'yBias', 'zBias',
        'xrateGV', 'yrateGV', 'zrateGV',
        'rate_delay', 'yaw', 'pitch', 'roll',
        'latitude', 'longitude', 'elevation',
        'sunAz', 'sunZen', 'sunAzEx', 'sunZenEx',
        'radius', 'psi', 'theta', 'psiCont', 'thetaCont', 'psiOff', 'thetaOff', 'psiInit', 'thetaInit',
        'xOff', 'yOff', 'imgX', 'imgY',
        'serialFlag', 'driftCor', 'state',
        'Ix', 'Iy', 'tau',
        'mirModel', 'fogExtrap', 'overruns',
        'headroom', 'seqNum', 'status', 'temp', 'check'
    ]

    concatenated_df = None
    logs_read = 0
    for (root, dirs, files) in os.walk(dir, topdown=True):
        for idx, file in enumerate(sorted(files)):
            if idx < start_idx:
                continue
            if logs_to_cat:
                if logs_read > logs_to_cat:
                    continue

            with open(os.path.join(dir, file), 'rb') as f:
                text = f.read()

            rows = []
            for i in range(lines_per_file):
                row_idx = i * bytes_per_row
                try:
                    index = struct.unpack(">" + "f", text[row_idx:row_idx + single_size])
                    doubles_idx = row_idx + single_size
                    doubles = struct.unpack(">" + "d" * doubles_per_row, text[doubles_idx:doubles_idx + doubles_per_row * double_size])
                    singles_idx = row_idx + single_size + doubles_per_row * double_size
                    singles = struct.unpack(">" + "f" * singles_per_row, text[singles_idx:singles_idx + singles_per_row * single_size])
                    rows.append(index + doubles + singles)
                except struct.error:
                    print("Stab log line parsing error!")
                    continue

            df = pd.DataFrame(rows, columns=cols)

            # Skip the dummy data
            if idx == len(files) - 1:
                logging.info(f"Cutting {len(df.loc[df['currentTime'] == -9999])} rows of dummy data.")
                df = df.loc[df['currentTime'] != -9999]

            logging.info(f"{file}: Start: {int(df['ind'][0])}, End: {int(df['ind'].iloc[-1])}")
            if concatenated_df is None:
                concatenated_df = df
            else:
                concatenated_df = pd.concat([concatenated_df, df], ignore_index=True)

            logs_read += 1

    # fractional days since 1601: row.winTime/86400 + datetime(1601, 1, 1).timestamp()
    # UTC: seconds since 1970-01-01
    # (days since 1601 - days since 1970) * 86400
    # datetime(1601, 1, 1).timestamp() == seconds before 1970-01-01
    # winTime == seconds since 1601-01-01
    logging.info("Generating utcTime column for the stab dataframe.")
    concatenated_df['utcTime'] = concatenated_df.apply(lambda r: r.winTime + datetime(1601, 1, 1, tzinfo=timezone.utc).timestamp(), axis=1)

    # Interpolate the UTC times based on an assumed steady program rate.
    logging.info(f"Interpolating stab UTC times based on a program rate of {program_rate} Hz.")
    start_step = concatenated_df.ind[0]
    start_time = concatenated_df.utcTime[0]
    concatenated_df['utcTimeInt'] = concatenated_df.apply(
        lambda r: start_time + (r.ind - start_step) * (1 / program_rate),
        axis=1
    )

    # Calculate gyro rate magnitude across all three axes
    logging.info("Generating gyro_mag column for the stab dataframe.")
    concatenated_df['gyro_mag'] = concatenated_df.apply(
        lambda r: np.linalg.norm([r.gyroX, r.gyroY, r.gyroZ]),
        axis=1
    )

    logging.info("Wrapping yaw to +- 180 degrees.")
    concatenated_df['yaw_wrapped'] = concatenated_df.apply(
        lambda r: wrap.to_180(r.yaw), axis=1
    )

    # for col in ['gyroX', 'gyroY', 'gyroZ']:
    #     logging.info(f"Calculating gyro acceleration for {col}.")
    #     concatenated_df[f'{col}_acc'] = concatenated_df[col].diff()

    # logging.info("Generating ypr_mag column for the stab dataframe.")
    # concatenated_df['ypr_mag'] = concatenated_df.apply(
    #     lambda r: np.linalg.norm([r.yaw_wrapped, r.pitch, r.roll]),
    #     axis=1
    # )

    return concatenated_df
