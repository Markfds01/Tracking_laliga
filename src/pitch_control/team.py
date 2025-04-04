import numpy as np
import pandas as pd

from src.data.utils import find_goalkeeper
from src.pitch_control.player import Player


class Team:
    """
    Class defining a team object that creates and stores all players together with some
    global information for the team

    __init__ Parameters
    -----------
    team_name: team name "home" or "away"
    first_frame: first frame of the dataframe
    params: dictionary containing all the model parameters
    include_individual_velocities: flag to indicate if individual max velocities should be used
    individual_velocities: dataframe with the maximum velocity of each player

    methods include:
    -----------
    get_goalkeeper_id: obtains the goalkeeper id using information from the first frame
    initialize_players: initializes and stores all the players in the team
    update_players: updates the position and velocity of all players for the frame
    update_players_time_to_intercept: updates the time to intercept at the position for all players
    get_players_inframe: returns the list of players in the frame
    """

    def __init__(self, team_name, first_frame, params, include_individual_velocities=False,
                 individual_velocities=None, stamine_plus=None):
        self.params = params
        self.name = team_name
        self.gk_id, self.team_half = self.get_goalkeeper_id(first_frame)
        self.possession = None
        self.players = self.initialize_players(first_frame, include_individual_velocities,
                                               individual_velocities, stamine_plus)
        self.PPCF = None
        # Initialize the position and velocities, not really necessary
        self.update_players(first_frame)

    def get_goalkeeper_id(self, first_frame):
        """Returns the id of the goalkeeper"""
        goalkeepers,team_pitch_halfs = find_goalkeeper(first_frame)
        gk_id = goalkeepers[self.name]
        team_half = team_pitch_halfs[self.name]
        #print(f'the pitch of the {self.name} is {team_pitch_halfs[self.name]}')
        return gk_id,team_half

    def initialize_players(self, first_frame, include_individual_velocities, individual_velocities,
                           stamine_factor=None):
        """Initializes all players and stores them in a list"""
        player_ids = np.unique([c.split('_')[1] for c in first_frame.keys() if c[:4] == self.name])

        team_players = []
        for p in player_ids:
            team_player = Player(p, self.name, self.params, p == self.gk_id,
                                 include_individual_velocities, individual_velocities,
                                 stamine_factor)
            team_players.append(team_player)
        return team_players

    def update_players(self, frame_data):
        """Updates the possession of the team and the position and velocities of the players"""
        self.possession = 'attacking' if self.name == frame_data['ball_owner'].iloc[
            0] else 'defending'
        for player in self.players:
            player.update_player(frame_data)

    def update_players_time_to_intercept(self, r_final):
        """Updates the time to intercept to r_final for all players"""
        for player in self.players:
            player.update_time_to_intercept(r_final)

    def get_players_inframe(self):
        """Returns the list of players currently in the frame"""
        players_list = [player for player in self.players if player.inframe]
        return players_list

    def update_players_PCCF(self,flag):
        for player in self.players:
            player.PPCF_total += player.PPCF

            if self.team_half == 'left' and self.possession == 'attacking':
                if flag=='first':
                    player.PPCF_attacking_first_zone += player.PPCF
                elif flag=='second':
                    player.PPCF_attacking_second_zone += player.PPCF
                elif flag=='third':
                    player.PPCF_attacking_third_zone += player.PPCF
            elif self.team_half == 'right' and self.possession == 'attacking':
                if flag=='first':
                    player.PPCF_attacking_third_zone += player.PPCF
                elif flag=='second':
                    player.PPCF_attacking_second_zone += player.PPCF
                elif flag=='third':
                    player.PPCF_attacking_first_zone += player.PPCF
            elif self.team_half == 'left' and self.possession == 'defending':
                if flag=='first':
                    player.PPCF_defending_first_zone += player.PPCF
                elif flag=='second':
                    player.PPCF_defending_second_zone += player.PPCF
                elif flag=='third':
                    player.PPCF_defending_third_zone += player.PPCF
            elif self.team_half == 'right' and self.possession == 'defending':
                if flag=='first':
                    player.PPCF_defending_third_zone += player.PPCF
                elif flag=='second':
                    player.PPCF_defending_second_zone += player.PPCF
                elif flag=='third':
                    player.PPCF_defending_first_zone += player.PPCF


        

    def get_players_vmax(self):
        velocities = []
        for player in self.players:
            velocities.append({'id': player.id,
                               'team': self.name,
                               'vmax': player.vmax})

        return pd.DataFrame(velocities)
