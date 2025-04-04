from pathlib import Path
import pandas as pd
import numpy as np
import sys


def process_match(match_number, part):
    """
    Removes all players with team or jersey number = -1
    """
    print(f'Processing match {match_number} part {part}')

    filename = f'DATOS/tracking/Aclean{part}_{match_number}.csv'
    if not Path.is_file(Path(filename)):
        sys.exit(f'The file {match_number} does not exist in data/raw')

    data = pd.read_csv(filename, header=None)

    # Process player data
    team_mapping = {
        '0': 'away',
        '1': 'home',
        '3': 'referee',
        '4': 'none'
    }

    jerseys_positions = np.arange(3, 175, 6)

    grouped_dfs = []
    for jersey in jerseys_positions:
        group = data.iloc[:, [0, jersey - 2, jersey, jersey + 1, jersey + 2]]
        group.columns = ['frame', 'team', 'jersey', 'position_x', 'position_y']
        grouped_dfs.append(group)

    long_df = pd.concat(grouped_dfs)
    long_df = long_df[long_df['jersey'] != -1]
    long_df['team'] = long_df['team'].astype(int).astype(str).map(team_mapping)
    long_df['team_jersey'] = long_df['team'] + '_' + long_df['jersey'].astype(int).astype(str)
    long_df.drop(['team', 'jersey'], axis=1, inplace=True)

    df = data.iloc[:, 0].to_frame('frame')
    for player in long_df['team_jersey'].unique():
        player_df = long_df.loc[
            long_df['team_jersey'] == player, ['frame', 'position_x', 'position_y']]
        player_df.columns = ['frame', f'{player}_x', f'{player}_y']
        df = df.merge(player_df, on='frame', how='left')

    # Process ball data
    ball_mapping = {
        '1': 'home',
        '2': 'away'
    }
    ball_df = data.iloc[:, [0, -1, -2, -3, -4, -5, -6]]
    ball_df.columns = ['frame', 'ball_status', 'ball_owner', 'ball_speed',
                       'ball_z', 'ball_y', 'ball_x']
    ball_df_copy = ball_df.copy()  # just to get rid of the annoying warning
    ball_df_copy.loc[:, 'ball_owner'] = ball_df['ball_owner'].astype(int).astype(str).map(
        ball_mapping)

    df = df.merge(ball_df_copy, on='frame', how='left')

    Path('data/processed').mkdir(exist_ok=True)
    df.to_csv(f'data/processed/Aclean{part}_{match_number}.csv', index=False)

    print('Done!')

    return df
