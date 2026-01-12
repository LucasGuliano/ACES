import os

import pandas as pd
from matplotlib import pyplot as plt

from aces_reader.mimic_log_parser import parse_mimic_logs


def test_parse_mimic_logs(fixtures):
    mimic_log_dir = os.path.join(fixtures, 'mimic_logs')
    mimic_df = parse_mimic_logs(mimic_log_dir)['df']
    assert isinstance(mimic_df, pd.DataFrame)
    assert len(mimic_df) == 120000

    # Show that the utcTimes are choppy
    counter = 0
    for idx in range(len(mimic_df.utcTime) - 1):
        if mimic_df.utcTime[idx + 1] - mimic_df.utcTime[idx]:
            counter += 1

    # Only 24970 of 120k samples have unique utcTimes
    assert counter == 24970

    # Show that the interpolated utcTimes are well-sampled
    for idx in range(len(mimic_df.utcTimeInt) - 1):
        assert round(mimic_df.utcTimeInt[idx + 1] - mimic_df.utcTimeInt[idx], 3) == 1 / 1000

    plt.figure()
    plt.plot(
        mimic_df.time - mimic_df.time[0],
        mimic_df.utcTime - mimic_df.utcTime[0],
        label=f"utcTime", alpha=0.7
    )
    plt.plot(
        mimic_df.time - mimic_df.time[0],
        mimic_df.utcTimeInt - mimic_df.utcTimeInt[0],
        label=f"utcTime Interpolated", alpha=0.7
    )

    plt.xlabel('Time (s)')
    plt.ylabel('utcTime (s)')
    plt.title(f"utcTimes v. Time")
    plt.legend()
