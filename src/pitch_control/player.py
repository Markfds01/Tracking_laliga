import numpy as np


class Player:
    """
    Class defining a player object that stores position, velocity, time-to-intercept and
    pitch control contributions for a player

    __init__ Parameters
    -----------
    pid: id (jersey number) of player
    teamname: team name "home" or "away"
    params: dictionary of model parameters
    is_gk: flag to indicate if he is the goalkeeper
    include_individual_velocities: flag to indicate if individual max velocities should be used
    individual_velocities: dataframe with the maximum velocity of each player

    methods include:
    -----------
    update_player(frame_data): updates the position and velocity for that frame
    simple_time_to_intercept(r_final): time take for player to get to target position (r_final)
    probability_intercept_ball(T): probability player will have controlled ball at time T
    """

    def __init__(self, pid, teamname, params, is_gk, include_individual_velocities=False,
                 individual_velocities=None, stamine_factor=None):
        self.id = pid
        self.is_gk = is_gk
        self.tagname = "%s_%s_" % (teamname, pid)
        self.vmax = individual_velocities.loc[self.id]['percentile_vel'] \
            if include_individual_velocities else params['max_player_speed']
        self.reaction_time = params['reaction_time']
        self.tti_sigma = params['tti_sigma']  # (see Eq 4 in Spearman, 2018)
        self.lambda_att = params['lambda_att']  # (see Eq 4 in Spearman, 2018)
        self.lambda_def = params['lambda_gk'] if self.is_gk else params['lambda_def']
        self.constant_value = -np.pi / np.sqrt(3.0) / self.tti_sigma
        # Variables that should be updated each frame
        self.PPCF_total = 0
        self.PPCF_attacking_first_zone = 0
        self.PPCF_attacking_second_zone = 0
        self.PPCF_attacking_third_zone = 0
        self.PPCF_defending_first_zone = 0
        self.PPCF_defending_second_zone = 0
        self.PPCF_defending_third_zone = 0
        self.PPCF = None
        self.velocity = None
        self.inframe = None
        self.position = None
        # Variables that should be updated for each cell
        self.time_to_intercept = None

    def update_player(self, frame_data):
        """Updates the position and velocity for the given frame"""
        self.position = np.array([frame_data[f'{self.tagname}x'].iloc[0],
                                  frame_data[f'{self.tagname}y'].iloc[0]])
        self.inframe = not np.any(np.isnan(self.position))
        self.velocity = np.array([frame_data[f'{self.tagname}vx'].iloc[0],
                                  frame_data[f'{self.tagname}vy'].iloc[0]])
        if np.any(np.isnan(self.velocity)):
            self.velocity = np.array([0., 0.])

    def update_time_to_intercept(self, r_final):
        """Estimates the time to intercept the ball at position r_final. Assumes that the player
        continues at current velocity for 'reaction_time' seconds and then runs at full speed"""
        # Not the cleanest way, but this will reset it for each cell
        self.PPCF = 0
        # TODO: what if the player is heading already towards the ball and
        #  gets there within reaction_time?
        r_reaction = self.position + self.velocity * self.reaction_time
        self.time_to_intercept = (self.reaction_time + np.linalg.norm(r_final - r_reaction) /
                                  self.vmax)

    def probability_intercept_ball(self, T):
        """Probability of a player arriving at target location at time T given their expected
        time to intercept as described in Spearman 2018"""
        # Change to improve performance
        # f = 1 / (1. + np.exp(-np.pi / np.sqrt(3.0) / self.tti_sigma * (T - self.time_to_intercept)))
        # TODO time to intercept
        f = 1 / (1. + np.e ** (self.constant_value * (T - self.time_to_intercept)))
        return f

