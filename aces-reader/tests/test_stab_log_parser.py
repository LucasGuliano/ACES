import os

import pandas as pd
from matplotlib import pyplot as plt

from aces_reader.stab_log_parser import parse_stab_logs


def test_read_stab_log(fixtures):
    stab_log_dir = os.path.join(fixtures, 'stab_logs')
    stab_df = parse_stab_logs(stab_log_dir)
    assert isinstance(stab_df, pd.DataFrame)
    assert len(stab_df) == 50272

    # Show that the utcTimes are choppy
    counter = 0
    for idx in range(len(stab_df.utcTime) - 1):
        if stab_df.utcTime[idx + 1] - stab_df.utcTime[idx]:
            counter += 1

    # Only 499 of 50k samples have unique utcTimes
    assert counter == 499

    # Show that the interpolated utcTimes are well-sampled
    for idx in range(len(stab_df.utcTimeInt) - 1):
        assert round(stab_df.utcTimeInt[idx + 1] - stab_df.utcTimeInt[idx], 3) == 1 / 1000

    plt.figure()
    plt.plot(
        stab_df.currentTime - stab_df.currentTime[0],
        stab_df.utcTime - stab_df.utcTime[0],
        label=f"utcTime", alpha=0.7
    )
    plt.plot(
        stab_df.currentTime - stab_df.currentTime[0],
        stab_df.utcTimeInt - stab_df.utcTimeInt[0],
        label=f"utcTime Interpolated", alpha=0.7
    )

    plt.xlabel('Time (s)')
    plt.ylabel('utcTime (s)')
    plt.title(f"utcTimes v. Time")
    plt.legend()
