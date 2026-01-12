import logging
from datetime import datetime

import numpy as np


def get_sliding_stdd(df, seconds_per_segment, data_col, step=100, program_rate=2000):
    """
    NB this probably only works for the mimic logs right now. Generalize it later.
    """
    col = f'stdd_{data_col}'
    df[col] = np.nan
    for i in range(0, len(df[data_col]), step):
        if i + seconds_per_segment * program_rate < len(df[data_col]):
            this_sliding_value = df[data_col].loc[i:i + seconds_per_segment * program_rate].std()

            df.loc[i, col] = this_sliding_value

    return df


def get_sliding_mean(df, seconds_per_segment, data_cols, step=100, program_rate=2000):
    logging.info(f"Calculating sliding mean of {seconds_per_segment}s every {step} steps.")
    for col in data_cols:
        sliding_col = f'sliding_mean_{col}'
        df[sliding_col] = np.nan
        for i in range(program_rate*seconds_per_segment, len(df[col]), step):
            if i + seconds_per_segment * program_rate < len(df[col]):
                this_sliding_value = df[col].loc[i - seconds_per_segment * program_rate:i].mean()

                df.loc[i, sliding_col] = this_sliding_value

    return df


def align_stab_to_mimic_df(stab_df, mimic_df, search_over=1, program_rate=2000, truncate=True):
    """
    Find the closest UTC time in the stab log to the mimic log.
    Assume that the gyro log was started before the mimic log.
    Assume that an alignment will occur in `search_over` seconds.
    """
    logging.info("Attempting to align mimic and stab log timestamps.")
    min_diff = np.inf
    min_idx = 0
    mimic_t0 = mimic_df.utcTimeInt[0]
    original_stab_t0 = stab_df.utcTimeInt[0]
    # Get up to 0.1s away from alignment.
    if mimic_t0 - original_stab_t0 < 0:
        # Skip to 0.1 second after the stab timestamp begins.
        shifted_mimic_idx = int((original_stab_t0 - mimic_t0 + 0.1) * program_rate)
        mimic_df = mimic_df.iloc[shifted_mimic_idx:].reset_index()
        mimic_t0 = mimic_df.utcTimeInt[0]
    else:
        # Skip the stab log to 0.1s before the mimic timestamp begins.
        # Stab. runs at 1000Hz
        shifted_stab_idx = int((mimic_t0 - original_stab_t0 - 0.1) * 1000)
        stab_df = stab_df.iloc[shifted_stab_idx:].reset_index()

    # Do an iterative search to find the closest alignment.
    for idx, stab_utc in enumerate(stab_df.utcTimeInt.loc[stab_df.utcTimeInt - stab_df.utcTimeInt[0] <= search_over]):
        this_diff = abs(stab_utc - mimic_t0)
        if this_diff < min_diff:
            min_diff = this_diff
            min_idx = idx

        # Might work
        if this_diff > min_diff:
            logging.info(f"Diff is starting to grow from min diff of {min_diff} at idx {idx}.")
            break

    stab_df = stab_df.iloc[min_idx:].reset_index()
    logging.info(
        f"Aligned stab. dataframe to mimic dataframe:\n"
        f"mimic t0:    {mimic_t0:.6f}, {datetime.utcfromtimestamp(mimic_t0)}\n"
        f"stab t0:     {original_stab_t0:.6f}, {datetime.utcfromtimestamp(original_stab_t0)}\n"
        f"new stab t0: {stab_df.utcTimeInt[0]:.6f}, {datetime.utcfromtimestamp(stab_df.utcTimeInt[0])}"
    )

    if truncate:
        logging.debug("Truncating the dataframes to be the same length.")
        if len(stab_df) > int(len(mimic_df)/(program_rate/1000)):
            stab_df = stab_df[:int(len(mimic_df)/(program_rate/1000))]
        else:
            mimic_df = mimic_df[:int(len(stab_df)*(program_rate/1000))]

    return stab_df, mimic_df
