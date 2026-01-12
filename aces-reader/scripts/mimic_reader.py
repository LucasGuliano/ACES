"""
Used to decode binary logs from `mimic`.

take std dev of the derivative in the leg sections
optionally: add a 60 Hz sine wave to part of the measurement to see if it maps

take std dev. of keyence noise sitting still
 - with motor closed loop at a fixed position
 - with a fixed mirror and keyence sensor clamped to a common substrate

make slides of some graphs and the tests  performed, take pictures of the setup with the clamping

- make std dev truly running -- only shift one sample per std dev
-- running mean too
- last data sweep too

"""
import logging
import os

import matplotlib as mpl
import matplotlib.pyplot as plt

from aces_reader import utilities
from aces_reader.mimic_log_parser import parse_mimic_logs

mpl.rcParams['agg.path.chunksize'] = 10000
alpha = 0.7
import numpy as np

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)


# def plot_set_measured_dac(n, df, unique_part_of_title):
#     plt.figure(n)
#
#     plt.plot(df['times'], df['positions_0'], label="Measured Points")
#     plt.plot(df['times'], df['voltages'], label="DAC Voltages")
#     # plt.plot(x, np.array(x) * m + b, '--k', label=f"Fit: Micrometers = {m:.2f}*Voltage + {b:.2f}")
#     plt.xlabel('Time (s)')
#     plt.ylabel('Position (mm)')
#     plt.title(f"{unique_part_of_title} Positions v. Time. {len(df['times'])} points. {(df['times'].values[-1] - df['times'].values[0]) / 60:.2f} minutes of sweeping.")
#     plt.legend()
#     # plt.ylim(-7, 7)
#
#     plt.figure(n + 1)
#     sample_len = 1 / 1000
#     first_gradient = np.gradient(df['positions_0'], sample_len)
#     plt.plot(df['times'] - df['times'].values[0], first_gradient,
#              label="Velocity")
#     plt.title(f"{unique_part_of_title} velocity of measured positions.")
#     plt.xlabel('Time (s)')
#     plt.ylabel('Velocity (mm/s)')
#     # plt.ylim(-15, 15)
#
#     # plt.figure(n+2)
#     # samples_per_segment = 1000
#     # df['velocities'] = first_gradient
#     # print(f"Calculating sliding std. dev. with {samples_per_segment} samples per segment.")
#     # velocity_sttd = get_stdds(df, samples_per_segment, data_col='velocities', step=samples_per_segment)
#     # plt.plot(velocity_sttd['times'],
#     #          velocity_sttd['std_ds'], label="Std. Deviation over velocity.")
#     # plt.title(f"Standard deviation of velocity; over {samples_per_segment} samples every {samples_per_segment} points")
#     # plt.xlabel('Time (s)')
#     # plt.ylabel('Standard Deviation (mm/s)')
#     # plt.ylim(0, 8)
#
#     # plt.figure(n+3)
#     # subset = df.loc[df['times'].between(1255.2, 1256.2)]
#     # plt.plot(subset['times'], subset['positions_0'] - subset['set_points'], label="\"noise\"")
#     # plt.plot(subset['times'], np.gradient(subset['positions_0'] - subset['set_points'], sample_len), label='Gradient')
#     # plt.legend()
#     # plt.xlabel('Time (s)')
#     # plt.ylabel('Measured - Set Point (mm)')


# def compare_data(n, first, second, info, open_loop_offset=0, closed_loop_offset=8.8):
#     # Compare the slope of each
#     plt.figure(n + 1)
#     sample_len = 1 / 430
#     first_gradient = np.gradient(first['measured_positions'], sample_len)
#     second_gradient = np.gradient(second['measured_positions'], sample_len)
#
#     samples_per_segment = 100
#     stdd_gradient_first = get_stdds(pd.DataFrame(data=zip(first['times'].values, first_gradient), columns=['times', 'gradient']), samples_per_segment, data_col_name='gradient')
#     stdd_gradient_second = get_stdds(pd.DataFrame(data=zip(second['times'].values, second_gradient), columns=['times', 'gradient']), samples_per_segment, data_col_name='gradient')
#     mean_gradient_first = get_stdds(pd.DataFrame(data=zip(first['times'].values, first_gradient), columns=['times', 'gradient']), samples_per_segment, data_col_name='gradient', means=True)
#     mean_gradient_second = get_stdds(pd.DataFrame(data=zip(second['times'].values, second_gradient), columns=['times', 'gradient']), samples_per_segment, data_col_name='gradient', means=True)
#     plt.plot(first['times'] - first['times'].values[0], first_gradient,
#              label="Shrouded Gradient with electronics on foam (1)")
#     plt.plot(second['times'] - second['times'].values[0], second_gradient,
#              label="Shrouded Gradient with electronics on foam and laptop isolated (2)")
#     plt.plot(stdd_gradient_first['times'] - first['times'].values[0], stdd_gradient_first['std_ds'],
#              label="Std. Deviation over (1) instantaneous velocities.")
#     plt.plot(stdd_gradient_second['times'] - second['times'].values[0], stdd_gradient_second['std_ds'],
#              label="Std. Deviation over (2) instantaneous velocities.")
#     plt.plot(mean_gradient_first['times'] - first['times'].values[0], mean_gradient_first['std_ds'],
#              label="Mean over (1) instantaneous velocities.")
#     plt.plot(mean_gradient_second['times'] - second['times'].values[0], mean_gradient_second['std_ds'],
#              label="Mean over (2) instantaneous velocities.")
#     plt.legend()
#     plt.title("Derivatives of the measured positions with moving std. deviation.")
#     plt.xlabel("Time")
#     plt.ylabel("um / s")
#     # plt.ylim(-110, 110)
#
#     # For kicks, add a 60 Hz wave
#     y = 0.2 * np.sin(second['times'].values * 2 * math.pi * 60)
#
#     plt.figure(n)
#     plt.plot(first['times'] - first['times'].values[0], first['measured_positions'] + open_loop_offset, label="Shroud Measurements")
#     plt.plot(second['times'] - second['times'].values[0], second['measured_positions'] + closed_loop_offset, label="No Shroud Measurements")
#     # plt.plot(second['times'] - second['times'].values[0], y, label="Supposed 60 Hz Noise")
#     plt.xlabel('Seconds since run start')
#     plt.ylabel('Micrometers')
#     plt.title(f"Second Table.\n"
#               f"Measured Positions v. Time. {len(second['times'])} points. {(second['times'].values[-1] - second['times'].values[0]) / 60:.2f} minutes.\n"
#               # f"Std. Deviation: Open: {statistics.stdev(df['measured_positions']):.4f}, Closed: {statistics.stdev(second['measured_positions']):.4f}\n"
#               f"Kp: 1e-4, Kd: 1e-5")
#
#     # Get the stddev across segments
#     # stdd_positions_first = get_stdds(first, samples_per_segment)
#
#     # plt.plot(stdd_positions_first['times'] - first['times'].values[0], stdd_positions_first['std_ds'], label="Std. Deviation over shroud positions")
#     plt.legend()
#     # plt.ylim(-110, 110)


def plot_comparisons(dfs, plots):
    # Supported plots: ['error', 'velocity', 'velocity stdd']
    if 'error' in plots:
        plt.figure()
        for title, df in dfs.items():
            plt.plot(df['times'] - df['times'].values[0], df['position_0'] - df['set_points'],
                     label=f"{title} Error", alpha=alpha)

        plt.xlabel('Time (s)')
        plt.ylabel('Position - Set Point (mm)')
        plt.title(f"Error v. Time")
        plt.legend()

    if 'velocity' in plots:
        plt.figure()
        counter = 1
        for title, df in dfs.items():
            sample_len = 1 / (1000 * counter)
            first_gradient = np.gradient(df['position_0'], sample_len)
            df['velocities'] = first_gradient
            plt.plot(df['time'] - df['time'].values[0], first_gradient,
                     label=f"{title} Velocity", alpha=alpha)
            counter += 1

        plt.xlabel('Time (s)')
        plt.ylabel('Velocity (mm/s)')
        plt.title(f"Velocity v. Time")
        plt.legend()

    if 'velocity stdd' in plots:
        plt.figure()
        seconds_per_segment = 1
        step = 1000
        counter = 1
        for title, df in dfs.items():
            logging.info(f"For {title}, calculating sliding std. dev. with {seconds_per_segment} seconds per segment every {step} program steps.")
            velocity_sttd = utilities.get_sliding_stdd(df, seconds_per_segment, 'velocities', step=step, program_rate=counter*1000)
            plt.plot(velocity_sttd['time'], velocity_sttd['std_ds'],
                     label=f"{title} Std. Deviation of velocity (mm/s).", alpha=alpha)
            counter += 1

        plt.title(f"Standard deviation of velocity; over {seconds_per_segment}s every {step} program steps")
        plt.xlabel('Time (s)')
        plt.ylabel('Standard Deviation (mm/s)')
        plt.legend()


if __name__ == '__main__':
    # High level directory where the subfolders with metrology logs are stored
    if os.name == 'nt':
        data_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
    else:
        #data_dir = os.path.join(os.path.expanduser('~'), 'Code', 'ACES', 'data', 'TF03')
        data_dir = os.path.join(os.path.expanduser('~'), 'ACES', 'log_files')

    logs_to_cat = 100
    '''dfs = {
        "1000Hz Program Rate": parse_mimic_logs(os.path.join(data_dir, '1000hz-program-rate'), logs_to_cat=logs_to_cat)['df'],
        "2000Hz Program Rate": parse_mimic_logs(os.path.join(data_dir, '2000hz-program-rate'), logs_to_cat=logs_to_cat)['df'],
        "3000Hz Program Rate": parse_mimic_logs(os.path.join(data_dir, '3000hz-program-rate'), logs_to_cat=logs_to_cat)['df'],
    }'''
    
    dfs = {"2000Hz Program Rate": parse_mimic_logs(os.path.join(data_dir))['df']}
    
    # dfs = {
    #     "Takeoff 1kHz Program Rate": parse_log_files(os.path.join(data_dir, 'takeoff-1000hz'), logs_to_cat=logs_to_cat)['df'],
    #     "Landing 2kHz Program Rate": parse_log_files(os.path.join(data_dir, 'landing-2000hz'), logs_to_cat=logs_to_cat)['df'],
    # }

   #plot_comparisons(dfs, ['velocity', 'velocity stdd'])
    plot_comparisons(dfs, ['velocity'])

    plt.show()
