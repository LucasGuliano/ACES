import logging
import os
from datetime import datetime, timedelta

import numpy as np
from matplotlib import pyplot as plt

from aces_reader import mimic_log_parser, stab_log_parser, utilities

alpha = 0.7

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)


def plot_comparisons(mimic_dfs, stab_dfs, plots):
    gyro_field = 'gyro_mag'
    if 'interpolated time' in plots:
        plt.figure()
        for title, df in mimic_dfs.items():
            plt.plot(
                df.time - df.time[0],
                df.utcTime - df.utcTime[0],
                label=f"{title} mimic utcTime", alpha=alpha
            )
            plt.plot(
                df.time - df.time[0],
                df.utcTimeInt - df.utcTimeInt[0],
                label=f"{title} mimic utcTime Interpolated", alpha=alpha
            )

        for title, df in stab_dfs.items():
            plt.plot(
                df.currentTime - df.currentTime[0],
                df.utcTime - df.utcTime[0],
                label=f"{title} stab utcTime", alpha=alpha
            )
            plt.plot(
                df.currentTime - df.currentTime[0],
                df.utcTimeInt - df.utcTimeInt[0],
                label=f"{title} stab utcTime Interpolated", alpha=alpha
            )

        plt.xlabel(f"Interpolated UTC Time, relative from starting point (s)")
        plt.ylabel('utcTime (s)')
        plt.title(f"utcTimes v. Time")
        plt.legend()

    if 'position' in plots:
        plt.figure()
        for title, df in mimic_dfs.items():
            plt.plot(df['utcTimeInt'] - df['utcTimeInt'][0], df['position_0'],
                     label=f"{title} Position at t0: {datetime.utcfromtimestamp(df['utcTimeInt'][0])}", alpha=alpha)

        for title, df in stab_dfs.items():
            gyro_scale = 1
            plt.plot(df['utcTimeInt'] - df['utcTimeInt'][0], df[gyro_field]*gyro_scale,
                     label=f"{title} {gyro_field}x{gyro_scale} at t0: {datetime.utcfromtimestamp(df['utcTimeInt'][0])}", alpha=alpha)

        plt.xlabel(f"Interpolated UTC Time, relative from starting point (s)")
        plt.ylabel('Position (mm)')
        plt.title(f"Position v. Time")
        plt.legend()

    gyro_scale = 2
    if 'velocity' in plots:
        plt.figure()
        counter = 1
        for title, df in mimic_dfs.items():
            plt.plot(df['utcTimeInt'] - df['utcTimeInt'].values[0], df['velocity'],
                     label=f"{title} Velocity", alpha=alpha)
            counter += 1

        for title, df in stab_dfs.items():
            plt.plot(df['utcTimeInt'] - df['utcTimeInt'].loc[0],
                     df[gyro_field]*gyro_scale,
                     label=f"{title} {gyro_field}x{gyro_scale}", alpha=alpha)

        plt.xlabel(f"Interpolated UTC Time, relative from starting point (s)")
        plt.ylabel('Velocity (mm/s)')
        plt.title(f"Velocity v. Time")
        plt.legend()

    if 'stdd' in plots:
        plt.figure()
        seconds_per_segment = 1
        step = 1000
        counter = 1
        for title, df in mimic_dfs.items():
            logging.info(f"For {title}, calculating sliding std. dev. with {seconds_per_segment} seconds per segment every {step} program steps.")
            df = utilities.get_sliding_stdd(df, seconds_per_segment, 'velocity', step=step, program_rate=counter * 1000)
            df = df.loc[~df['stdd_velocity'].isnull()]
            plt.plot(df['utcTimeInt'] - df['utcTimeInt'][0], df['stdd_velocity'],
                     label=f"{title} Std. Deviation of velocity (mm/s) at t0: {datetime.utcfromtimestamp(df['utcTimeInt'][0])}", alpha=alpha)
            counter += 1

        counter = 1
        for title, df in stab_dfs.items():
            logging.info(f"For {title}, calculating sliding std. dev. with {seconds_per_segment} seconds per segment every {step} program steps. Gyro scale: {gyro_scale}")
            df = utilities.get_sliding_stdd(df, seconds_per_segment, gyro_field, step=step, program_rate=1000)
            df = df.loc[~df[f'stdd_{gyro_field}'].isnull()]
            plt.plot(df['utcTimeInt'] - df['utcTimeInt'][0], df[f'stdd_{gyro_field}']*gyro_scale,
                     label=f"{title} Std. Deviation of {gyro_field}, x{gyro_scale} at t0: {datetime.utcfromtimestamp(df['utcTimeInt'][0])}", alpha=alpha)
            counter += 1

        plt.title(f"Standard deviation of velocity; over {seconds_per_segment}s every {step} program steps.")
        plt.xlabel(f"Interpolated UTC Time, relative from starting point (s)")
        plt.ylabel('Standard Deviation (mm/s)')
        plt.legend()

    if 'ypr' in plots:
        logging.info("Plotting yaw, pitch, and roll (centered over zero) vs position.")
        plt.figure()
        segment_offset = 65
        segment_len = 60
        t0 = df.utcTimeInt[0]
        for title, df in mimic_dfs.items():
            segment_start = df.utcTimeInt[0] + segment_offset
            df = df.loc[df.utcTimeInt.between(segment_start, segment_start + segment_len)].reset_index()
            plt.plot(
                df['utcTimeInt'] - df['utcTimeInt'][0],
                df['position_0'] - df['position_0'].mean(),
                label=f"{title} Position centered at 0\nt0: {datetime.utcfromtimestamp(df['utcTimeInt'][0])}", alpha=alpha
            )
            plt.plot(
                df['utcTimeInt'] - df['utcTimeInt'][0],
                df['voltage'],
                label=f"{title} Voltage", alpha=alpha
            )

        for title, df in stab_dfs.items():
            segment_start = df.utcTimeInt[0] + segment_offset
            df = df.loc[df.utcTimeInt.between(segment_start, segment_start + segment_len)].reset_index()

            seconds_per_segment = 1
            step = 10
            df = utilities.get_sliding_mean(df, seconds_per_segment, ['gyroX', 'gyroY', 'gyroZ'], step=step, program_rate=1000)
            scale = 30
            df = df.loc[~df['sliding_mean_gyroX'].isnull()].reset_index(drop=True)
            plt.plot(
                df.utcTimeInt - df.utcTimeInt[0],
                (df.sliding_mean_gyroX - df.sliding_mean_gyroX.mean())*scale,
                label=f"{title} sliding avg. gyroX, centered at 0\nt0: {datetime.utcfromtimestamp(df['utcTimeInt'][0])}", alpha=alpha
            )
            plt.plot(
                df.utcTimeInt - df.utcTimeInt[0],
                (df.sliding_mean_gyroY - df.sliding_mean_gyroY.mean())*scale,
                label=f"{title} sliding avg. gyroY, centered at 0.", alpha=alpha
            )
            plt.plot(
                df.utcTimeInt - df.utcTimeInt[0],
                (df.sliding_mean_gyroZ - df.sliding_mean_gyroZ.mean())*scale,
                label=f"{title} sliding avg. gyroZ, centered at 0.", alpha=alpha
            )

        plt.title(f"Position, Gyro Rate Accelerations (Scaled by {scale}, Averaged {seconds_per_segment}s backward every {step} points) vs. Time.")
        plt.xlabel(f"Interpolated UTC Time (s), relative from starting point of {segment_len}s subset at {t0:.3f} + {segment_offset}s")
        plt.legend()


if __name__ == '__main__':
    # High level directory where the subfolders with metrology logs are stored
    if os.name == 'nt':
        data_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
    else:
        data_dir = os.path.join(os.path.expanduser('~'), 'Code', 'ACES', 'data')

    # 2024-04-06 TF05 Control loop parameter and tau comparison
    logs_to_cat = 40
    mimic_dir = os.path.join(data_dir, 'TF05', 'met_logs')
    # Note that we're running at 2kHz in mimic as of the end of TF03, so we need half as many stab logs.
    stab_dir = os.path.join(data_dir, 'TF05', 'stab_logs')
    test_cases = {
        # "1622 4 2 0.07": 45,
        # doesn't handle turbulence well
        # "1625 kd 0.08": 51,
        # "1629 tau 0.2": 59,
        # "1632 tau 0.3": 65,
        # "1635 tau 0.4": 71,
        # "1639 tau 0.5": 79,
        # "1642 kp 4.1, tau 0.2": 85,
        # "1645 kp 4.1 tau 0.4": 91,
        # lots of turbulence
        # "1648 4 2 0.07 tau 0.4": 97,
        # "1704 kp 4.1, tau 0.4": 131,
        "1742 zero set point open loop": 204,
        "1746 zero setpoint closed loop": 212,
    }

    mimic_dfs = {}
    stab_dfs = {}
    for test_case, offset in test_cases.items():
        mimic_dfs.update({
            test_case: mimic_log_parser.parse_mimic_logs(
             os.path.join(mimic_dir, test_case), logs_to_cat=logs_to_cat)['df']
        })
        stab_dfs.update({
            test_case: stab_log_parser.parse_stab_logs(
            # The +2 comes from the metUEI's ~one-minute earlier, internal, UTC time (until TF04?).
            stab_dir, logs_to_cat=int(logs_to_cat/2) + 2, start_idx=offset)
        })

    for idx, stab_df_key in enumerate(stab_dfs.keys()):
        stab_dfs[stab_df_key], mimic_dfs[stab_df_key] = \
            utilities.align_stab_to_mimic_df(stab_dfs[stab_df_key], mimic_dfs[stab_df_key])

    plot_comparisons(mimic_dfs, stab_dfs, ['stdd'])
    plt.show()

    # # 2024-04-03 TF04 Control loop parameter comparison
    # logs_to_cat = 10
    # mimic_dir = os.path.join(data_dir, 'TF04', 'met_logs')
    # # Note that we're running at 2kHz in mimic as of the end of TF03, so we need half as many stab logs.
    # stab_dir = os.path.join(data_dir, 'TF04', 'stab_logs')
    # test_cases = {
    #     "1729 4 2 0.07": 205,
    #     "1905 4 2 0.06": 398,
    # }

    # 2024-03-29 FF01 Control loop parameter comparison
    # logs_to_cat = 20
    # mimic_dir = os.path.join(data_dir, 'FF01', 'met-logs')
    # # Note that we're running at 2kHz in mimic as of the end of TF03, so we need half as many stab logs.
    # stab_dir = os.path.join(data_dir, 'FF01', 'stab-logs')
    # test_cases = {
    #     "1901 NORMAL 4 2 0.05": 81,
    #     # This one is worse than the normal case on average (visual inspection).
    #     # "1910 4.2 2 0.05": 101,
    #     "1915 4 2 0.07": 111,
    #     # Worse than #4
    #     # "1922 4 2.3 0.07": 127,
    #     # Worse than #4, better than #2
    #     # "1924 4 1.8 0.07": 131,
    #     # "1926 3.8 2 0.07": 133,
    #     # Worse than #4, about the same as #2. You get smoothness but a generally higher std. dev.
    #     # "1930 3.6 2 0.07": 141,
    #     # "1933 4.2 2 0.07": 147,
    #     "1936 NORMAL 4 2 0.05": 152,
    # }

    # 2024-03-27 TF02 Position to Gyro / Yaw + Pitch + Roll comparison
    # logs_to_cat = 50
    # start_idx = 190
    # mimic_dir = os.path.join(data_dir, 'TF02', 'mimic-logs')
    # mimic_dfs = {
    #     "Takeoff to Elevation": mimic_log_parser.parse_mimic_logs(
    #         mimic_dir, logs_to_cat=logs_to_cat, start_idx=start_idx)['df'],
    # }
    #
    # stab_dir = os.path.join(data_dir, 'TF02', 'stab-logs')
    # stab_dfs = {
    #     "Takeoff to Elevation": stab_log_parser.parse_stab_logs(
    #         stab_dir, logs_to_cat=logs_to_cat, start_idx=start_idx),
    # }
    #
    # for idx, stab_df_key in enumerate(stab_dfs.keys()):
    #     stab_dfs[stab_df_key], mimic_dfs[stab_df_key] = \
    #         utilities.align_stab_to_mimic_df(stab_dfs[stab_df_key], mimic_dfs[stab_df_key])
    #
    # plot_comparisons(mimic_dfs, stab_dfs, ['position', 'ypr'])

    # 2024-03-27 TF03 program rate comparison
    # mimic_dir = os.path.join(data_dir, 'TF03')
    # mimic_dfs = {
    #     "1000Hz Program Rate": mimic_log_parser.parse_log_files(
    #         os.path.join(mimic_dir, '1000hz-program-rate'), logs_to_cat=logs_to_cat)['df'],
    #     "2000Hz Program Rate": mimic_log_parser.parse_log_files(
    #         os.path.join(mimic_dir, '2000hz-program-rate'), logs_to_cat=logs_to_cat)['df'],
    #     "3000Hz Program Rate": mimic_log_parser.parse_log_files(
    #         os.path.join(mimic_dir, '3000hz-program-rate'), logs_to_cat=logs_to_cat)['df'],
    # }
    #
    # stab_dir = os.path.join(data_dir, 'TF03', 'stab-logs')
    # stab_dfs = {
    #     "1000Hz Program Rate": stab_log_parser.read_stab_log(os.path.join(stab_dir, '1000hz-program-rate'), logs_to_cat=logs_to_cat),
    #     "2000Hz Program Rate": stab_log_parser.read_stab_log(os.path.join(stab_dir, '2000hz-program-rate'), logs_to_cat=logs_to_cat),
    #     "3000Hz Program Rate": stab_log_parser.read_stab_log(os.path.join(stab_dir, '3000hz-program-rate'), logs_to_cat=logs_to_cat)
    # }
