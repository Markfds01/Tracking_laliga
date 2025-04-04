import pickle
import pandas as pd
import re
from pathlib import Path
from parser import parse_args
import src.data.utils as utils
from src.data import analysis
from src.pitch_control.pitch_control import PitchControl
from tqdm import tqdm

DATA_PATH = Path('data/processed')


# TODO: sacar goalkeeperes y size del campo del XML


def estimate_single_frame(filename, frame, include_velocities=False):
    """Estimate pitch control in a single frame"""
    df, home_velocities, away_velocities = utils.prepare_df(DATA_PATH / (filename + '.csv'))

    # Estimate pitch control
    if frame not in df['frame'].values:
        raise Exception('Frame not found in match')

    if include_velocities:
        pitch_control = PitchControl(df, include_individual_velocities=True,
                                     home_individual_velocities=home_velocities,
                                     away_individual_velocities=away_velocities)
    else:
        pitch_control = PitchControl(df)

    PPCFa = pitch_control.generate_pitch_control_for_event(df.loc[df['frame'] == frame])
    data = pitch_control.get_individual_contributions()

    output = {
        'match': filename,
        'frame': frame,
        'PPCFa': PPCFa,
        'individual_contributions': data
    }
    pickle_file = Path('results') / f'single_frame_{filename}_{frame}.pkl'
    with open(pickle_file, 'wb') as f:
        pickle.dump(output, f)


def calculate_one_half(filename, frames_step, include_velocities=False,
                       home_stamine_factor=None, away_stamine_factor=None,
                       positions_to_increase = ['Defender','Midfielder','Striker','Substitute']):
    # read and process the data
    df, home_velocities, away_velocities = utils.prepare_df(DATA_PATH / (filename + '.csv'), filename,frames_step,
                                                            include_player_velocities=include_velocities,
                                                            stamine_home=home_stamine_factor,
                                                            stamine_away=away_stamine_factor,
                                                            positions_to_increase=positions_to_increase)

    # Initialite the teams


    pitch_control = PitchControl(df, include_individual_velocities=True, 
                                     home_individual_velocities=home_velocities,
                                     away_individual_velocities=away_velocities,
                                     home_stamine_factor=home_stamine_factor,
                                     away_stamine_factor=away_stamine_factor)

    if any(pd.isnull(df['frame'])):
        exit(f'There are some NaNs in the frames!')

    PPCF_array = []

    # Calculate the contributions for each frame
    print('Optimized code with love and a sprinkle of magic ✨')
    leng = len(df)
    for frame in tqdm(df['frame'], desc='Analyzing Frames'):
        _ = pitch_control.generate_pitch_control_for_event(df.loc[df['frame'] == frame])
        data = pitch_control.get_individual_contributions()
        PPCF_array.append(data)

    PPCF_concatenated = pd.concat(PPCF_array, ignore_index=True)
    result_df = PPCF_concatenated.groupby(['id', 'team']).agg({
        'PPCF': 'sum',
        'PPCF_attacking_first_zone': 'sum',
        'PPCF_attacking_second_zone': 'sum',
        'PPCF_attacking_third_zone': 'sum',
        'PPCF_defending_first_zone': 'sum',
        'PPCF_defending_second_zone': 'sum',
        'PPCF_defending_third_zone': 'sum'
    }).reset_index()
    velocities_df = pitch_control.get_vmax_df()
    result_df = result_df.merge(velocities_df, on=['id', 'team'], how='left')

    output = {
        'match': filename,
        'match_id': re.search(r'\d+$', filename).group(),
        'individual_contributions': result_df
    }
    if len(positions_to_increase)==4:
        filename = utils.create_output_filename(f'one_half_{filename}', include_velocities,
                                            home_stamine_factor, away_stamine_factor)
        
    else:
        filename = utils.create_output_filename(f'one_half_{filename}', include_velocities,
                                            home_stamine_factor, away_stamine_factor,positions=positions_to_increase)
    print(f'filename es : {filename}')

    pickle_file = Path('results') / f'{filename}.pkl'
    with open(pickle_file, 'wb') as f:
        pickle.dump(output, f)


if __name__ == "__main__":
    args = parse_args()

    if args.single_frame:
        estimate_single_frame(args.filename, args.single_frame, args.include_velocities)
    else:
        if args.multiple_frames:
            for frame in args.multiple_frames:
                estimate_single_frame(args.filename, frame)
            analysis.sum_mutiple_frames_contributions(args.filename, args.multiple_frames)
        else:
            if args.one_half:
                if args.position_increase:
                    calculate_one_half(args.filename, args.one_half,
                                    include_velocities=args.include_velocities,
                                    home_stamine_factor=args.stamine_home,
                                    away_stamine_factor=args.stamine_away,
                                    positions_to_increase=args.position_increase)
                else:
                    calculate_one_half(args.filename, args.one_half,
                                    include_velocities=args.include_velocities,
                                    home_stamine_factor=args.stamine_home,
                                    away_stamine_factor=args.stamine_away)
            else:
                exit('Please, enter a valid option')
