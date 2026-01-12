

import csv
import logging
import os
import time

import matplotlib.pyplot as plt


def concat_labjack_files():
    file_suffixes = range(2, 5)
    data = []
    total = 0
    for file_suffix in file_suffixes:
        with open(os.path.join(os.path.dirname(__file__), f'data_{file_suffix}.dat')) as f:
            tsv_file = csv.reader(f, delimiter="\t")
            for idx, line in enumerate(tsv_file):
                # line 4: ['Time', 'v0', 'v1', 'v2', 'v3', 'y0', 'y1', 'y2', 'y3']
                # line 5:: ['23.996000', '0.399383', '4.187644', '4.167429', '1.827008', '0.399383', '4.187644', '4.167429', '1.827008']
                if idx > 5 and len(line) == 9 and float(line[0]) and float(line[2]) and float(line[3]):
                    diff = abs(float(line[3]) - float(line[2]))
                    total += diff
                    data.append([float(line[0]), float(line[2]), float(line[3]), diff])

    return data, total

def plot_labjack():
    data, total = concat_labjack_files()

    average = total / len(data)

    t = [d[0] for d in data]
    v_in = [d[1] for d in data]
    v_out = [d[2] for d in data]

    plt.plot(t, v_in, label='v_in')
    plt.plot(t, v_out, label='v_out')

    plt.xlabel('LabJack T7 Sample')
    plt.ylabel('Voltage')
    plt.title('Input vs. Output voltage from Mirror Controller')
    plt.legend()

    plt.show()


def parse_keyence_csv():
    data = []
    with open(os.path.join(os.path.dirname(__file__), 'point_five.csv')) as f:
        csv_file = csv.reader(f)
        for idx, line in enumerate(csv_file):
            data.append([idx, float(line[2])])

    return data


def plot_keyence():
    data = parse_keyence_csv()

    samples = [d[0] for d in data]
    positions = [d[1] for d in data]
    stop_idx = int(704047)
    ideal_positions = []
    ideal_slope = (data[stop_idx][1] - data[0][1]) / (data[stop_idx][0] - data[0][0])
    for idx, sample in enumerate(samples[:stop_idx]):
        ideal_positions.append(ideal_slope*idx + data[0][1])

    plt.plot(samples, positions, label='measured')
    plt.plot(samples[:stop_idx], ideal_positions, label='ideal-ish')

    plt.xlabel('Keyence Sample (2.55 us / sample)')
    plt.ylabel('Position (mm?)')
    plt.title('Keyence readout, Voltage step: 0.000039')
    plt.legend()
    # Reduce the ticks on the y axis
    # plt.figure().get_axes().locator_params(axis='y', nbins=6)
    plt.show()
    # ax = plt.gca()
    # ax.set_xlim([xmin, xmax])
    # ax.set_ylim([-110, 110])
    # plt.ylim(-110, 110)



if __name__ == "__main__":
    start = time.time()
    # plot_labjack()
    plot_keyence()
    logging.info(f"Plotted in {time.time() - start} s.")
