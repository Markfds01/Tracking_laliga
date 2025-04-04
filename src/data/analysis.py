import pickle
from pathlib import Path
import pandas as pd


def sum_mutiple_frames_contributions(match, frames):
    PPCF_array = []
    for frame in frames:
        with open(f'results/single_frame_{match}_{frame}.pkl', 'rb') as f:
            single_frame = pickle.load(f)
        PPCF_dataframe = single_frame['individual_contributions']
        PPCF_array.append(PPCF_dataframe)
    PPCF_concatenated = pd.concat(PPCF_array, ignore_index=True)
    result_df = PPCF_concatenated.groupby(['id', 'team'])['PPCF'].sum().reset_index()
    filename = Path('analysis') / f'single_frame_{match}_contributions.csv'
    result_df.to_csv(filename, index=False)
