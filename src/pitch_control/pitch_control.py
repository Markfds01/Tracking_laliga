import numpy as np
import pandas as pd
from src.pitch_control.team import Team


class PitchControl:
    """
    Creates a pitch control object that will initialize and store the teams and their players

    __init__ Parameters
    -----------
    tracking_df: the whole tracking dataframe
    include_individual_velocities: flag to indicate if individual max velocities should be used
    individual_velocities: dataframe with the maximum velocity of each player
    field_dimen: x and y size of the field in meters
    n_grid_cells_x: number of cells in the horizontal dimension

    methods include:
    -----------
    calculate_cells: estimates the size of the cells in both directions
    generate_pitch_control_for_event: estimates pitch control for the frame
    calculate_pitch_control_at_target: estimates pitch control for a single cell
    update_player(frame_data): updates the position and velocity for that frame
    simple_time_to_intercept(r_final): time take for player to get to target position (r_final)
    probability_intercept_ball(T): probability player will have controlled ball at time T
    """

    def __init__(self, tracking_df,
                 include_individual_velocities=False, home_individual_velocities=None,
                 away_individual_velocities=None, home_stamine_factor=None, away_stamine_factor=None,
                 field_dimen=(106., 68.,), n_grid_cells_x=50):
        self.field_dimen = field_dimen
        self.n_grid_cells_x = n_grid_cells_x
        self.n_grid_cells_y = None
        self.xgrid = None
        self.ygrid = None
        self.first_zone = None
        self.second_zone = None
        self.third_zone = None
        # This will populate n_grid and xygrid
        self.calculate_cells()

        # Varios parameters
        self.params = {
            'max_player_accel': 7,
            'max_player_speed': 5,
            'reaction_time': 0.7,
            'tti_sigma': 0.45,
            'kappa_def': 1.,
            'lambda_att': 4.3,
            'average_ball_speed': 15.,
            'time_to_control_def': None,
            'time_to_control_att': None,
            'int_dt': 0.04,
            'max_int_time': 50,
            'model_converge_tol': 0.01,
            'time_to_control_veto': 3
        }

        # Computed parameters
        self.params['lambda_def'] = 4.3 * self.params['kappa_def']
        self.params['lambda_gk'] = self.params['lambda_def'] * 3.0
        self.params['time_to_control_att'] = self.params['time_to_control_veto'] * np.log(10) * (
                np.sqrt(3) * self.params['tti_sigma'] / np.pi + 1 / self.params['lambda_att'])
        self.params['time_to_control_def'] = self.params['time_to_control_veto'] * np.log(10) * (
                np.sqrt(3) * self.params['tti_sigma'] / np.pi + 1 / self.params['lambda_def'])

        # Store each team
        self.team_home = Team('home', tracking_df.head(1), self.params,
                              include_individual_velocities, home_individual_velocities,
                              home_stamine_factor)
        self.team_away = Team('away', tracking_df.head(1), self.params,
                              include_individual_velocities, away_individual_velocities,
                              away_stamine_factor)

    def calculate_cells(self):
        self.n_grid_cells_y = int(self.n_grid_cells_x * self.field_dimen[1] / self.field_dimen[0])
        dx = self.field_dimen[0] / self.n_grid_cells_x
        self.xgrid = np.arange(self.n_grid_cells_x) * dx - self.field_dimen[0] / 2. + dx / 2.
        dy = self.field_dimen[1] / self.n_grid_cells_y
        self.ygrid = np.arange(self.n_grid_cells_y) * dy - self.field_dimen[1] / 2. + dy / 2.

        self.first_zone = len(self.xgrid) / 3.
        self.second_zone = len(self.xgrid) / 3. * 2
        self.third_zone = len(self.xgrid)
        
    def generate_pitch_control_for_event(self, frame_data, offsides=True):
        """
        Evaluates pitch control surface over the entire field at the given frame

        Parameters
        -----------
        frame_data: tracking dataframe of a single frame for both teams with positions
        offsides: If True, find and remove offside atacking players from the calculation.
            Default is True.

        Returns
        -----------
        PPCFa: Pitch control surface (dimen (n_grid_cells_x,n_grid_cells_y) ) containing pitch
            control probability for the attcking team. Surface for the defending team is 1-PPCFa.
        """

        # Update information for the current frame
        ball_position = [frame_data['ball_x'].iloc[0], frame_data['ball_y'].iloc[0]]

        self.team_home.update_players(frame_data)
        self.team_away.update_players(frame_data)

        attacking_team = self.team_home if self.team_home.possession == 'attacking' else self.team_away
        defending_team = self.team_home if self.team_home.possession == 'defending' else self.team_away

        # Keep only players in frame
        attacking_players = attacking_team.get_players_inframe()
        defending_players = defending_team.get_players_inframe()

        # Find any attacking players that are offside and remove them from calculation
        if offsides:
            attacking_players = check_offsides(attacking_players, defending_players,
                                               ball_position, defending_team.gk_id)

        # Initialise pitch control grids for attacking and defending teams
        PPCFa = np.zeros(shape=(len(self.ygrid), len(self.xgrid)))
        PPCFd = np.zeros(shape=(len(self.ygrid), len(self.xgrid)))

        # Calculate pitch control model at each location on the pitch
        for i in range(len(self.ygrid)):
            for j in range(len(self.xgrid)):
                target_position = np.array([self.xgrid[j], self.ygrid[i]])
                try:
                    # The time to intercept has to be updated for the rest of the algorithm
                    # this updates all the players even though we will only use the ones contained
                    # in attacking_players and defending_players. If we used attacking_team.players
                    # we would lose the inframe and offside filters
                    attacking_team.update_players_time_to_intercept(target_position)
                    defending_team.update_players_time_to_intercept(target_position)

                    flag = self.get_flag_zone(j)

                    PPCFa[i, j], PPCFd[i, j] = self.calculate_pitch_control_at_target(
                        target_position, attacking_players, defending_players, ball_position)

                    attacking_team.update_players_PCCF(flag)
                    defending_team.update_players_PCCF(flag)

                except (BallMissingError, ConvergenceError, ProbabilityEstimationError,
                        MissingGoalKeeper) as e:
                    raise AssertionError(f'Caught a custom exception {e} in frame {frame_data.frame.iloc[0]}')

        # Check probabilitiy sums within convergence
        checksum = np.sum(PPCFa + PPCFd) / float(self.n_grid_cells_y * self.n_grid_cells_x)
        if 1 - checksum > self.params['model_converge_tol']:
            raise AssertionError(f'Checksum failed {1 - checksum}')

        return PPCFa

    def calculate_pitch_control_at_target(self, target_position, attacking_players,
                                          defending_players, ball_position):
        """
        Calculates the pitch control probability for the attacking and defending teams at a
            specified target position on the ball.

        Parameters
        -----------
        target_position: size 2 numpy array containing the (x,y) position to evaluate pitch control
        attacking_players: list of players in the attacking team
        defending_players: list of players in the defending team
        ball_position: current position of the ball (start position for a pass).
            If set to NaN, function will assume that the ball is already at the target position.

        Returns
        -----------
        PPCFatt: Pitch control probability for the attacking team
        PPCFdef: Pitch control probability for the defending team
            ( 1-PPCFatt-PPCFdef <  params[model_converge_tol] )
        """
        if ball_position is None or any(np.isnan(ball_position)):
            raise BallMissingError('ball is not present in the frame')

        # Calculate ball travel time from start position to end position
        ball_travel_time = (np.linalg.norm(target_position - ball_position) /
                            self.params['average_ball_speed'])

        # Get players closest to the target to avoid calculation
        closest_player_att, tau_min_att = get_closest_player_to_current_position(attacking_players)
        closest_player_def, tau_min_def = get_closest_player_to_current_position(defending_players)

        # If the closest player from one team can arrive significantly before the other, no need
        # to solve the pitch control model
        if tau_min_att - max(ball_travel_time, tau_min_def) >= self.params['time_to_control_def']:
            closest_player_def.PPCF += 1
            return 0., 1.
        elif tau_min_def - max(ball_travel_time, tau_min_att) >= self.params['time_to_control_att']:
            closest_player_att.PPCF += 1
            return 1., 0.
        else:
            # Solve pitch control model by integrating equation 3 in Spearman et al.
            # First remove any player that is far (in time) from the target location
            # TODO: this won't really use the proper estimation for goalkeeps (lambda_gk)
            attacking_players = [p for p in attacking_players if
                                 p.time_to_intercept - tau_min_att < self.params[
                                     'time_to_control_att']]
            defending_players = [p for p in defending_players if
                                 p.time_to_intercept - tau_min_def < self.params[
                                     'time_to_control_def']]
            # Set up integration arrays
            dT_array = np.arange(ball_travel_time - self.params['int_dt'],
                                 ball_travel_time + self.params['max_int_time'],
                                 self.params['int_dt'])

            PPCF_attacking_team = np.zeros_like(dT_array)
            PPCF_defending_team = np.zeros_like(dT_array)

            # Integration equation 3 of Spearman 2018 until convergence or tolerance limit hit
            ptot = 0.0
            i = 1
            while 1 - ptot > self.params['model_converge_tol'] and i < dT_array.size:
                T = dT_array[i]
                for player in attacking_players + defending_players:
                    lambda_value = player.lambda_att if player in attacking_players else player.lambda_def

                    # Calculate ball control probablity for 'player' in time interval T+dt
                    dPPCFdT = ((1 - PPCF_attacking_team[i - 1] - PPCF_defending_team[i - 1]) *
                               player.probability_intercept_ball(T) * lambda_value)

                    # Make sure it's greater than zero
                    if dPPCFdT < 0:
                        raise ProbabilityEstimationError('Invalid player probability')

                    player.PPCF += dPPCFdT * self.params['int_dt']

                    if player in attacking_players:
                        PPCF_attacking_team[i] += player.PPCF
                    else:
                        PPCF_defending_team[i] += player.PPCF

                ptot = PPCF_defending_team[i] + PPCF_attacking_team[i]
                i += 1

            if i >= dT_array.size:
                raise ConvergenceError(f'Integration failed to converge: {ptot}')

            return PPCF_attacking_team[i - 1], PPCF_defending_team[i - 1]

    def get_individual_contributions(self):
        """Returns a dataframe with the individual contributions from each player in the frame"""
        player_attributes = []
        for player in self.team_home.players:
            player_attributes.append({
                'id': player.id,
                'team': self.team_home.name,
                'PPCF': player.PPCF_total,
                'PPCF_attacking_first_zone' : player.PPCF_attacking_first_zone,
                'PPCF_attacking_second_zone' : player.PPCF_attacking_second_zone,
                'PPCF_attacking_third_zone' : player.PPCF_attacking_third_zone,
                'PPCF_defending_first_zone' : player.PPCF_defending_first_zone,
                'PPCF_defending_second_zone' : player.PPCF_defending_second_zone,
                'PPCF_defending_third_zone' : player.PPCF_defending_third_zone
            })

        for player in self.team_away.players:
            player_attributes.append({
                'id': player.id,
                'team': self.team_away.name,
                'PPCF': player.PPCF_total,
                'PPCF_attacking_first_zone' : player.PPCF_attacking_first_zone,
                'PPCF_attacking_second_zone' : player.PPCF_attacking_second_zone,
                'PPCF_attacking_third_zone' : player.PPCF_attacking_third_zone,
                'PPCF_defending_first_zone' : player.PPCF_defending_first_zone,
                'PPCF_defending_second_zone' : player.PPCF_defending_second_zone,
                'PPCF_defending_third_zone' : player.PPCF_defending_third_zone
            })

        df = pd.DataFrame(player_attributes)
        return df

    def get_vmax_df(self):
        home_velocities_df = self.team_home.get_players_vmax()
        away_velocities_df = self.team_away.get_players_vmax()
        df = pd.concat([home_velocities_df, away_velocities_df], ignore_index=True)
        return df
    def get_flag_zone(self,j):
        # Check the zone and set the flag variable accordingly
        if j < self.first_zone:
            flag = 'first'
        elif self.first_zone <= j < self.second_zone:
            flag = 'second'
        elif self.second_zone <= j < self.third_zone:
            flag = 'third'
        else:
            flag = 'outside'
            raise outoffieldError('you are out of the field')
        return flag


class BallMissingError(Exception):
    pass


class ProbabilityEstimationError(Exception):
    pass


class ConvergenceError(Exception):
    pass


class MissingGoalKeeper(Exception):
    pass

class outoffieldError(Exception):
    pass


def check_offsides(attacking_players, defending_players, ball_position, defending_gk_id,
                   verbose=False, tol=0.2):
    """
    Checks whether any of the attacking players are offside (allowing for a tol margin of error).
    Offside players are removed from the 'attacking_players' list and ignored in the
    pitch control calculation.
    
    Parameters
    -----------
    attacking_players: list of players in the attacking team
    defending_players: list of players in the defending team
    ball_position: current position of the ball (start position for a pass).
        If set to NaN, function will assume that the ball is already at the target position
    defending_gk_id: defending goalkeeper id
    verbose: if True, print a message each time a player is found to be offside
    tol: A tolerance parameter that allows a player to be very marginally offside (up to tol m)
        without being flagged offside. Default: 0.2m

    Returns
    -----------
    attacking_players: list of 'player' objects for the players on the attacking team with offside
        players removed
    """
    if not any([defending_gk_id == p.id for p in defending_players]):
        raise MissingGoalKeeper('Missing goalkeeper in offside check')

    defending_GK = [p for p in defending_players if p.is_gk][0]
    # use defending goalkeeper x position to figure out which half he is defending (-1: left
    # goal, +1: right goal)
    defending_half = np.sign(defending_GK.position[0])
    # find the x-position of the second-deepest defeending player (including GK)
    second_deepest_defender_x = sorted([defending_half * p.position[0]
                                        for p in defending_players], reverse=True)[1]
    # define offside line as being the maximum of second_deepest_defender_x, ball position and
    # half-way line
    offside_line = max(second_deepest_defender_x, defending_half * ball_position[0], 0.0) + tol
    # any attacking players with x-position greater than the offside line are offside
    if verbose:
        for p in attacking_players:
            if p.position[0] * defending_half > offside_line:
                print("player %s in %s team is offside" % (p.id, p.playername))

    attacking_players = [p for p in attacking_players if
                         p.position[0] * defending_half <= offside_line]
    return attacking_players


def get_closest_player_to_current_position(players):
    """Returns the player closest to the current position and the time taken to get there"""
    time_to_intercept_list = [p.time_to_intercept for p in players]
    min_time_to_intercept = min(time_to_intercept_list)
    player_index = time_to_intercept_list.index(min_time_to_intercept)
    return players[player_index], min_time_to_intercept


