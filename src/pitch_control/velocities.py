import re
import numpy as np
import pandas as pd
import scipy.signal as signal
import src.data.utils as utils


def calculate_player_velocities(team, smoothing=True, filter_='moving-average', window=7,
                                polyorder=1, maxspeed=12):
    """
    Calculate player velocities in x & y direciton, and total player speed at each timestamp of the
    tracking data

    Parameters
    ----------
    team:  the complete tracking DataFrame
    smoothing: boolean variable that determines whether velocity measures are smoothed.
    filter_: type of filter to use when smoothing the velocities. Default is Savitzky-Golay,
    which fits a polynomial of order 'polyorder' to the data within each time-window
    window: smoothing window size in # of frames
    polyorder: order of the polynomial for the Savitzky-Golay filter. Default is 1 - a linear fit
    to the velcoity, so gradient is the acceleration
    maxspeed: the maximum speed that a player can realisitically achieve (in meters/second). Speed
    measures that exceed maxspeed are tagged as outliers and set to NaN.

    Returns
    -------
    The tracking DataFrame with columns for speed in the x & y direction and total speed added
    """

    player_ids = [x.group(1) for col in team.columns
                  if (x := re.match('((home|away)_[0-9]+)_x', col))]

    # Estimate velocities
    data = {}
    dt = team['time'].diff()
    for player in player_ids:
        vx = team[player + "_x"].diff() / dt
        vy = team[player + "_y"].diff() / dt
        

        # Remove unsmoothed data points that exceed the maximum speed
        # (these are most likely position errors)
        if maxspeed > 0:
            raw_speed = np.sqrt(vx ** 2 + vy ** 2)
            vx[raw_speed > maxspeed] = np.nan
            vy[raw_speed > maxspeed] = np.nan

        if smoothing:
            if filter_ == 'Savitzky-Golay':
                vx = signal.savgol_filter(vx, window_length=window, polyorder=polyorder)
                vy = signal.savgol_filter(vy, window_length=window, polyorder=polyorder)
            elif filter_ == 'moving average':
                ma_window = np.ones(window) / window
                vx = np.convolve(vx, ma_window, mode='same')
                vy = np.convolve(vy, ma_window, mode='same')

        data[f'{player}_vx'] = pd.Series(vx, dtype=float)
        data[f'{player}_vy'] = pd.Series(vy, dtype=float)
        data[f'{player}_total_v'] = pd.Series(np.sqrt(vx ** 2 + vy ** 2), dtype=float)
        max_value = data[f'{player}_vx'].max()
        #print(f'max v : {max_value}')

    data = pd.DataFrame.from_dict(data)
    team = pd.concat((team, data), axis=1)

    return team


def get_velocity_dataframe(data):
    """
    Returns a dataframe with the total velocity of each player

    Parameters
    ----------
    data: tracking dataframe with velocities already calculated

    Returns
    -------
    A dataframe with the velocity of each player
    """
    if not any(data.columns.str.endswith('total_v')):
        raise 'Velocities not present in the dataframe. Did you run calculate_player_velocities?'

    players = utils.get_jersey_team(data)

    df_list = []
    for (player, team) in players:
        df = pd.DataFrame({
            'jersey': player,
            'team': team,
            'velocity': data[f'{team}_{player}_total_v']
        })
        df_list.append(df)

    df = pd.concat(df_list, ignore_index=True)
    return df


def calculate_player_vmax(tracking_df, home_player_positions, away_player_positions,
                           positions_to_increase = ['Defender','Midfielder','Striker','Substitute'],
                          include_player_velocities = False,
                          percentile=95, GK_percentile=99,
                          stamine_home = 1.0,
                          stamine_away = 1.0):
    """
    Obtains the percentile velocity of each player for both teams

    Parameters
    ----------
    tracking_df: tracking dataframe with velocities already calculated
    percentile: percentile to use for normal players (from 0 to 100)
    GK_percentile: percentile to use for the goalkeepers

    Returns
    -------
    Two dataframes, one for each team, containing the percentile velocity of each player
    """

    def get_velocities_team(player_ids, data, team, stamine_dict,position_dict,positions_to_increase):
        team_data = []

        #Go through the players
        for player in player_ids:
            #Compute the percentiles
            team_velocity = data[f'{team}_{player}_total_v'].dropna()

            #Apply the stamine factor only to the positions
            if stamine_dict[team]:
                team_percentile = np.percentile(team_velocity, percentile) * stamine_dict[team] \
                    if position_dict[team].loc[player]['position'] in positions_to_increase else \
                        np.percentile(team_velocity, percentile)
            else:
                team_percentile = np.percentile(team_velocity, percentile)

            #GK more percentile
            if player == GK_ids[team]:
                team_percentile = np.percentile(team_velocity, GK_percentile)
            team_data.append(team_percentile)
        return team_data
    
    def apply_stamine_specific_positions(players_ids,team,stamine_dict,position_dict,positions_to_increase):
        team_data = []
        for player in players_ids:
            if stamine_dict[team]:
                team_percentile = 5 * stamine_dict[team] \
                    if position_dict[team].loc[player]['position'] in positions_to_increase \
                        else 5
            else:
                team_percentile = 5
            team_data.append(team_percentile)
        return team_data

    #Creating dicts for home and away
    stamine_dict = {
        'home' : stamine_home,
        'away' : stamine_away
    }

    position_dict = {
        'home' : home_player_positions,
        'away' : away_player_positions
    }

    home_player_ids = home_player_positions.index
    away_player_ids = away_player_positions.index
    # Obtain the ids of the goalkeepers
    GK_ids,_ = utils.find_goalkeeper(tracking_df)


    # Create dataframes for both teams
    if include_player_velocities:
        home_velocities = pd.DataFrame({'percentile_vel': get_velocities_team(home_player_ids,
                                                                            tracking_df,
                                                                            'home',stamine_dict,position_dict,
                                                                            positions_to_increase)},
                                    index=home_player_ids)
        away_velocities = pd.DataFrame({'percentile_vel': get_velocities_team(away_player_ids,
                                                                            tracking_df,
                                                                            'away',stamine_dict,position_dict,
                                                                            positions_to_increase)},
                                    index=away_player_ids)
    else:
        home_velocities = pd.DataFrame({'percentile_vel': apply_stamine_specific_positions(home_player_ids,'home',
                                                                                           stamine_dict,position_dict,
                                                                                           positions_to_increase)},
                                        
                                        index=home_player_ids)
            
        away_velocities = pd.DataFrame({'percentile_vel': apply_stamine_specific_positions(away_player_ids,'away',
                                                                                           stamine_dict,position_dict,
                                                                                           positions_to_increase)},
                                        
                                        index=away_player_ids)
    return home_velocities, away_velocities
