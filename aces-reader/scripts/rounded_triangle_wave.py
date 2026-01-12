import csv
import logging
import math
import os
import time

import numpy as np
import matplotlib.pyplot as plt


def generate_triangle_wave(x):
    """
    https://dsp.stackexchange.com/questions/35211/generating-smoothed-versions-of-square-wave-triangular-etc
    1.25−5cos−1((1−𝛿)sin(𝜋𝑥/3.2))/(2𝜋)
    :param amp:
    :param freq:
    :return:
    """
    d = []
    delta = 0.05  # Amplitude offset
    for sample in x:
        value = 1.25
        acos_term = (1 - delta) * math.sin(((1 / 3.4) * sample))
        value -= (5 * math.acos(acos_term)) / (2 * math.pi)
        d.append(value * 10)

    dydx = np.gradient(d, x[1] - x[0])

    return d, dydx


def generate_piecewise_triangle_wave(x, sample_rate):
    """
    By convention we consider the forward turnaround to be from -constant_amp to (-constant_amp - turnaround_amp) and
    back to -constant_amp. That is, we start with the negative turnaround for a smooth start/settling?
    :param x:
    :param sample_rate:
    :return:
    """
    sample_len = 1 / sample_rate

    # The triangular section length
    constant_len = 12.8  # seconds
    constant_amp = 9.95  # volts
    constant_slope = (2 * constant_amp) / constant_len

    # The smooth turnaround
    # volts in whole waveform +/- 10
    # Points in turnaround:
    turnaround_len = 0.2  # seconds

    samples_in_constants = constant_len / sample_len
    samples_in_turnarounds = turnaround_len / sample_len
    total_samples = 2 * samples_in_constants + 2 * samples_in_turnarounds

    y = []
    for idx, sample in enumerate(x):
        position_in_wave = idx % total_samples
        if position_in_wave < samples_in_turnarounds:
            # Forward turnaround
            shifted_x = (position_in_wave - samples_in_turnarounds) * sample_len
            a = constant_slope / turnaround_len
            b = constant_slope
            second_order_term = a * shifted_x ** 2
            first_order_term = b * shifted_x
            constant = -constant_amp
            parabola = second_order_term + first_order_term + constant
            y.append(parabola)
            continue

        if samples_in_turnarounds <= position_in_wave <= (samples_in_constants + samples_in_turnarounds):
            # Ascending constant
            mx = constant_slope * (position_in_wave * sample_len)
            turnaround_offset = constant_slope * turnaround_len
            b = -constant_amp - turnaround_offset
            y.append(mx + b)
            continue

        if (samples_in_constants + samples_in_turnarounds) < position_in_wave \
                < (2 * samples_in_turnarounds + samples_in_constants):
            # Backward turnaround
            shifted_x = \
                (position_in_wave
                 - (samples_in_turnarounds + samples_in_constants + samples_in_turnarounds)) \
                * sample_len
            a = -constant_slope / turnaround_len
            b = -constant_slope
            second_order_term = a * shifted_x ** 2
            first_order_term = b * shifted_x
            constant = constant_amp
            parabola = second_order_term + first_order_term + constant
            y.append(parabola)
            continue

        if (2 * samples_in_turnarounds + samples_in_constants) <= position_in_wave:
            # Descending Constant
            mx = -constant_slope * (position_in_wave * sample_len)
            preceding_offset = constant_slope * (2 * turnaround_len + constant_len)
            b = constant_amp + preceding_offset
            y.append(mx + b)

    y_gradient = np.gradient(y, sample_len)

    return y, y_gradient


def plot(x, piecewise, piecewise_gradient, wave, wave_gradient):
    plt.plot(x, piecewise, label='Piecewise Wave')
    plt.plot(x, piecewise_gradient, label='Piecewise Derivative')

    # plt.plot(x, wave, label='Sinuous Wave')
    # plt.plot(x, wave_gradient, label='Wave Derivative')

    plt.xlabel('Time (s)')
    plt.ylabel('Volts')
    plt.title('Rounded Triangular Wave')
    plt.legend()
    plt.grid(True)
    # plt.axis([51.5, 51.8, -10.2, -8.9])

    plt.show()


if __name__ == "__main__":
    start = time.time()
    amplitude = 1
    frequency = 1
    # TODO: Use third arg as sample rate, 2000 Hz?
    sample_rate = 2000
    x = np.arange(0, 120, 1 / sample_rate)
    piecewise, piecewise_gradient = generate_piecewise_triangle_wave(x, sample_rate)
    wave, wave_gradient = generate_triangle_wave(x)
    plot(x, piecewise, piecewise_gradient, wave, wave_gradient)
    logging.info(f"Plotted in {time.time() - start} s.")
