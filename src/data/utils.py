import re
import numpy as np
import pandas as pd


from src.pitch_control import velocities


def standardize_units(df):
    """Convert position from cm to m and time to seconds"""
    # Standardize position
    position_columns = [col for col in df.columns if
                        col.endswith('_x') or col.endswith('_y')]
    df[position_columns] /= 100

    # Standardize time
    df['time'] = [time * 0.04 for time in range(len(df))]

    return df


def get_jersey_team(data):
    """Returns the tuple (jersey,team) for each player"""
    player_ids = [(x.group(2), x.group(1)) for col in data.columns if
                  (x := re.match('(home|away)_([0-9]+)_x', col))]
    return player_ids


def get_ids_in_team(data, team='home'):
    """Returns the list of ids of players belonging to the a team"""
    player_ids = [x.group(1) for col in data.columns
                  if (x := re.match(f'{team}_([0-9]+)_x', col))]
    return player_ids


def initialite_players_contribution(home_metrics_df, away_metrics_df):
    # Initialize the length of each df
    home_num_rows = home_metrics_df.shape[0]
    away_num_rows = away_metrics_df.shape[0]

    # Add 'player_contribution' column to DataFrames and fill with zeros
    home_metrics_df['player_contribution'] = np.zeros((home_num_rows,))
    away_metrics_df['player_contribution'] = np.zeros((away_num_rows,))


def save_keeper(GK_ids, home_metrics_df, away_metrics_df):
    # Initialize the length of each df
    home_num_rows = home_metrics_df.shape[0]
    away_num_rows = away_metrics_df.shape[0]

    # Add 'player_contribution' column to DataFrames and fill with zeros
    home_metrics_df['keeper'] = np.zeros((home_num_rows,))
    away_metrics_df['keeper'] = np.zeros((away_num_rows,))

    home_metrics_df.loc[GK_ids['home']]['keeper'] = 1
    away_metrics_df.loc[GK_ids['away']]['keeper'] = 1


def remove_player(players, jersey_player_to_remove):
    players = [p for p in players if p.id != jersey_player_to_remove]

    return players


def find_goalkeeper(team):
    """Find the goalkeeper in team, identifying him/her as the player closest to goal at kick off"""
    # TODO what if the goalkeeper is substituted?
    x_columns = [c for c in team.columns if c[-2:].lower() == '_x' and c[:4] in ['home']]
    GK_col_home = team.iloc[0][x_columns].abs().astype(float).idxmax()
    GK_col_home_id = GK_col_home.split('_')[1]
    max_value_home = team.iloc[0][GK_col_home]
    symbol_home = 'left' if np.sign(max_value_home) == -1 else 'right' if np.sign(max_value_home) == 1 else ''


    x_columns = [c for c in team.columns if c[-2:].lower() == '_x' and c[:4] in ['away']]
    GK_col_away = team.iloc[0][x_columns].abs().astype(float).idxmax()
    GK_col_away_id = GK_col_away.split('_')[1]
    max_value_away = team.iloc[0][GK_col_away]
    symbol_away = 'left' if np.sign(max_value_away) == -1 else 'right' if np.sign(max_value_away) == 1 else ''

    GK_numbers = {'home': GK_col_home_id, 'away': GK_col_away_id}
    team_pich_halfs = {'home' : symbol_home, 'away': symbol_away}

    return GK_numbers,team_pich_halfs


def select_every_n_rows(df, n):
    selected_rows = df.iloc[::n]  # Select rows every block_size
    return selected_rows


def only_live_ball(df):
    df = df[df['ball_status'] == 1.0]

    return df


def find_index_from_frame(df, frame):
    condition_series = (df["frame"] == frame)

    # Find the index of the first True value in the condition_series
    index = condition_series.idxmax()
    return index


def min_and_max_frame(df):
    min_frame = df['frame'].min()
    max_frame = df['frame'].max()

    return min_frame, max_frame


def prepare_df(filepath,filename, frames_step=None,include_player_velocities=False,
               stamine_home=1.0,stamine_away=1.0 ,
               positions_to_increase = ['Defender','Midfielder','Striker','Substitute']):
    df = pd.read_csv(filepath)
    df = standardize_units(df)
    #print(len(df))
    df = velocities.calculate_player_velocities(df)
    if any(pd.isnull(df['frame'])):
        exit(f'There are some NaNs in the frames utils!')
    df = df[df['ball_status']==1]

    #Here as the user wont have the laliga data due to
    #the fact that it is not available to the public
    #we will have to create the player positions
    #for the home and away teams.
    #You can change the position as you want.
    home_positions = []
    away_positions = []
    set_indexes_home = set()
    set_indexes_away = set()
    for column in df.columns:
        if column.startswith('home'):
            shirt_number = column.split('_')[1]
            team = column.split('_')[0]
            if shirt_number not in set_indexes_home:
                home_positions.append({'index' : shirt_number, 'position' : 'Midfielder'})
                set_indexes_home.add(shirt_number)

        elif column.startswith('away'):
            shirt_number = column.split('_')[1]
            team = column.split('_')[0]

            if shirt_number not in set_indexes_away:
                away_positions.append({'index' : shirt_number, 'position' : 'Midfielder'})
                set_indexes_away.add(shirt_number)
    home_positions = pd.DataFrame(home_positions)
    home_positions.set_index('index', inplace=True)

    away_positions = pd.DataFrame(away_positions)
    away_positions.set_index('index', inplace=True)


    home_velocities, away_velocities = velocities.calculate_player_vmax(df, home_positions,away_positions, 
                                                                        include_player_velocities=include_player_velocities,
                                                                        stamine_home=stamine_home,stamine_away=stamine_away)
    

    merged_home_df = home_velocities.merge(home_positions,left_index = True,right_index=True)

    merged_away_df = away_velocities.merge(away_positions,left_index=True,right_index=True)

    if frames_step:
        df = select_every_n_rows(df, frames_step)
    return df, merged_home_df, merged_away_df


def create_output_filename(filename, include_velocities=None,
                           home_stamine_factor=None, away_stamine_factor=None,
                           positions=None):
    suffix = ''
    if include_velocities:
        suffix += '_include_velocities'
    if home_stamine_factor and not away_stamine_factor:
        suffix += f'_sh_{home_stamine_factor}_as_1.0'
    if away_stamine_factor and not home_stamine_factor:
        suffix += f'_sh_1.0_as_{away_stamine_factor}'
    if home_stamine_factor and away_stamine_factor:
        suffix += f'_sh_{home_stamine_factor}_as_{away_stamine_factor}'
    if positions:
        for position in positions:
            suffix += f'_{position}'
        

    return filename + suffix
