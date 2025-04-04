# -*- coding: utf-8 -*-
"""
Created on Tue Aug  8 19:33:10 2023

@author: Marco
"""
import re
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation


def plot_pitch(field_dimen=(106.0, 68.0), field_color='green', linewidth=2, markersize=20):
    """ plot_pitch
    
    Plots a soccer pitch. All distance units converted to meters.
    
    Parameters
    -----------
        field_dimen: (length, width) of field in meters. Default is (106,68)
        field_color: color of field. options are {'green','white'}
        linewidth  : width of lines. default = 2
        markersize : size of markers (e.g. penalty spot, centre spot, posts). default = 20
        
    Returrns
    -----------
       fig,ax : figure and aixs objects (so that other data can be plotted onto the pitch)

    """
    fig, ax = plt.subplots(figsize=(12, 8))  # create a figure
    # decide what color we want the field to be. Default is green, but can also choose white
    if field_color == 'green':
        ax.set_facecolor('green')
        lc = 'dodgerblue'  # line color
        pc = 'w'  # 'spot' colors
    elif field_color == 'white':
        lc = 'k'
        pc = 'k'
    # ALL DIMENSIONS IN m
    border_dimen = (3, 3)  # include a border arround of the field of width 3m
    meters_per_yard = 0.9144  # unit conversion from yards to meters
    half_pitch_length = field_dimen[0] / 2.  # length of half pitch
    half_pitch_width = field_dimen[1] / 2.  # width of half pitch
    signs = [-1, 1]
    # Soccer field dimensions typically defined in yards, so we need to convert to meters
    goal_line_width = 8 * meters_per_yard
    box_width = 20 * meters_per_yard
    box_length = 6 * meters_per_yard
    area_width = 44 * meters_per_yard
    area_length = 18 * meters_per_yard
    penalty_spot = 12 * meters_per_yard
    corner_radius = 1 * meters_per_yard
    D_length = 8 * meters_per_yard
    D_radius = 10 * meters_per_yard
    D_pos = 12 * meters_per_yard
    centre_circle_radius = 10 * meters_per_yard
    # plot half way line # center circle
    ax.plot([0, 0], [-half_pitch_width, half_pitch_width], lc, linewidth=linewidth)
    ax.scatter(0.0, 0.0, marker='o', facecolor=lc, linewidth=0, s=markersize)
    y = np.linspace(-1, 1, 50) * centre_circle_radius
    x = np.sqrt(centre_circle_radius ** 2 - y ** 2)
    ax.plot(x, y, lc, linewidth=linewidth)
    ax.plot(-x, y, lc, linewidth=linewidth)
    for s in signs:  # plots each line seperately
        # plot pitch boundary
        ax.plot([-half_pitch_length, half_pitch_length],
                [s * half_pitch_width, s * half_pitch_width], lc, linewidth=linewidth)
        ax.plot([s * half_pitch_length, s * half_pitch_length],
                [-half_pitch_width, half_pitch_width], lc, linewidth=linewidth)
        # goal posts & line
        ax.plot([s * half_pitch_length, s * half_pitch_length],
                [-goal_line_width / 2., goal_line_width / 2.], pc + 's',
                markersize=6 * markersize / 20., linewidth=linewidth)
        # 6 yard box
        ax.plot([s * half_pitch_length, s * half_pitch_length - s * box_length],
                [box_width / 2., box_width / 2.], lc, linewidth=linewidth)
        ax.plot([s * half_pitch_length, s * half_pitch_length - s * box_length],
                [-box_width / 2., -box_width / 2.], lc, linewidth=linewidth)
        ax.plot([s * half_pitch_length - s * box_length, s * half_pitch_length - s * box_length],
                [-box_width / 2., box_width / 2.], lc, linewidth=linewidth)
        # penalty area
        ax.plot([s * half_pitch_length, s * half_pitch_length - s * area_length],
                [area_width / 2., area_width / 2.], lc, linewidth=linewidth)
        ax.plot([s * half_pitch_length, s * half_pitch_length - s * area_length],
                [-area_width / 2., -area_width / 2.], lc, linewidth=linewidth)
        ax.plot([s * half_pitch_length - s * area_length, s * half_pitch_length - s * area_length],
                [-area_width / 2., area_width / 2.], lc, linewidth=linewidth)
        # penalty spot
        ax.scatter(s * half_pitch_length - s * penalty_spot, 0.0, marker='o', facecolor=lc,
                   linewidth=0, s=markersize)
        # corner flags
        y = np.linspace(0, 1, 50) * corner_radius
        x = np.sqrt(corner_radius ** 2 - y ** 2)
        ax.plot(s * half_pitch_length - s * x, -half_pitch_width + y, lc, linewidth=linewidth)
        ax.plot(s * half_pitch_length - s * x, half_pitch_width - y, lc, linewidth=linewidth)
        # draw the D
        y = np.linspace(-1, 1,
                        50) * D_length  # D_length is the chord of the circle that defines the D
        x = np.sqrt(D_radius ** 2 - y ** 2) + D_pos
        ax.plot(s * half_pitch_length - s * x, y, lc, linewidth=linewidth)

    # remove axis labels and ticks
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_xticks([])
    ax.set_yticks([])
    # set axis limits
    xmax = field_dimen[0] / 2. + border_dimen[0]
    ymax = field_dimen[1] / 2. + border_dimen[1]
    ax.set_xlim([-xmax, xmax])
    ax.set_ylim([-ymax, ymax])
    ax.set_axisbelow(True)
    fig.savefig('plots/pitch_mediumblue.svg', format='svg', bbox_inches='tight')

    return fig, ax


def plot_frame(tracking_df, index=1, figax=None, team_colors=('r', 'b'), field_dimen=(106.0, 68.0),
               include_player_velocities=False, PlayerMarkerSize=10, PlayerAlpha=0.7,
               annotate=False):
    """ plot_frame( hometeam, awayteam )
    
    Plots a frame of Metrica tracking data (player positions and the ball) on a football pitch. All distances should be in meters.
    
    Parameters
    -----------
        frame
        tracking_df: complete dataframe
        figax: Can be used to pass in the (fig,ax) objects of a previously generated pitch. Set to (fig,ax) to use an existing figure, or None (the default) to generate a new pitch plot,
        team_colors: Tuple containing the team colors of the home & away team. Default is 'r' (red, home team) and 'b' (blue away team)
        field_dimen: tuple containing the length and width of the pitch in meters. Default is (106,68)
        include_player_velocities: Boolean variable that determines whether player velocities are also plotted (as quivers). Default is False
        PlayerMarkerSize: size of the individual player marlers. Default is 10
        PlayerAlpha: alpha (transparency) of player markers. Defaault is 0.7
        annotate: Boolean variable that determines with player jersey numbers are added to the plot (default is False)
        
    Returrns
    -----------
       fig,ax : figure and aixs objects (so that other data can be plotted onto the pitch)

    """
    tracking_df = tracking_df.loc[index].to_frame().T

    if figax is None:  # create new pitch
        fig, ax = plot_pitch(field_dimen=field_dimen)
    else:  # overlay on a previously generated pitch
        fig, ax = figax  # unpack tuple
    # plot home & away teams in order
    for team, color in zip(['home', 'away'], team_colors):

        x_columns = [col for col in tracking_df.columns if re.match(f'{team}_[0-9]+_x', col)]
        y_columns = [col for col in tracking_df.columns if re.match(f'{team}_[0-9]+_y', col)]

        ax.plot(tracking_df[x_columns], tracking_df[y_columns], color=color,
                marker='o', markersize=PlayerMarkerSize, alpha=PlayerAlpha)  # plot player positions

        if include_player_velocities:
            print(tracking_df['away_3_vx'])
            vx_columns = [col for col in tracking_df.columns if re.match(f'{team}_[0-9]+_vx', col)]
            vy_columns = [col for col in tracking_df.columns if re.match(f'{team}_[0-9]+_vy', col)]

            ax.quiver(tracking_df[x_columns].astype(float), tracking_df[y_columns].astype(float),
                      tracking_df[vx_columns].astype(float), tracking_df[vy_columns].astype(float),
                      color=color, scale_units='inches', scale=10.,
                      width=0.0015, headlength=5, headwidth=3, alpha=PlayerAlpha)
        if annotate:
            [ax.text(tracking_df[x].iloc[0] + 0.5, tracking_df[y].iloc[0] + 0.5, x.split('_')[1],
                     fontsize=10, color=color)
             for x, y in zip(x_columns, y_columns)
             if not (np.isnan(tracking_df[x].values[0]) or np.isnan(tracking_df[y].values[0]))]

    # plot ball
    ax.plot(tracking_df['ball_x'], tracking_df['ball_y'], 'ko', markersize=6, alpha=1.0,
            linewidth=0)

    return fig, ax


def plot_pitchcontrol_for_event(index_of_row, pass_team_name, tracking_df, PPCF, alpha=0.7,
                                include_player_velocities=True, annotate=False,
                                field_dimen=(106.0, 68)):
    """ plot_pitchcontrol_for_event( event_id, events,  tracking_home, tracking_away, PPCF )
    
    Plots the pitch control surface at the instant of the event given by the event_id. Player and ball positions are overlaid.
    
    Parameters
    -----------
        tracking_df: (entire) tracking DataFrame for both teams
        PPCF: Pitch control surface (dimen (n_grid_cells_x,n_grid_cells_y) ) containing pitch control probability for the attcking team (as returned by the generate_pitch_control_for_event in Metrica_PitchControl)
        alpha: alpha (transparency) of player markers. Default is 0.7
        include_player_velocities: Boolean variable that determines whether player velocities are also plotted (as quivers). Default is False
        annotate: Boolean variable that determines with player jersey numbers are added to the plot (default is False)
        field_dimen: tuple containing the length and width of the pitch in meters. Default is (106,68)
        
    NB: this function no longer requires xgrid and ygrid as an input
        
    Returrns
    -----------
       fig,ax : figure and aixs objects (so that other data can be plotted onto the pitch)

    """

    # pick a pass at which to generate the pitch control surface
    # pass_frame = frame
    # pass_team = pass_team_name

    # plot frame and event
    fig, ax = plot_pitch(field_color='white', field_dimen=field_dimen)
    plot_frame(tracking_df, index_of_row, figax=(fig, ax), PlayerAlpha=alpha,
               include_player_velocities=include_player_velocities, annotate=annotate)

    # plot pitch control surface
    if tracking_df.loc[index_of_row]['ball_owner'] == 1.0:
        pass_team = 'home'
    else:
        pass_team = 'away'
    if pass_team == 'home':
        cmap = 'bwr'
    else:
        cmap = 'bwr_r'
    ax.imshow(np.flipud(PPCF), extent=(
        -field_dimen[0] / 2., field_dimen[0] / 2., -field_dimen[1] / 2., field_dimen[1] / 2.),
              interpolation='spline36', vmin=0.0, vmax=1.0, cmap=cmap, alpha=0.5)
    # Add colorbar
    # cbar = plt.colorbar(im, ax=ax)
    # cbar.set_label('Pitch Control Probability')
    return fig, ax


def save_match_clip(tracking_df, PPCF, fpath, fname='clip_test', figax=None, frames_per_second=25,
                    team_colors=('r', 'b'), field_dimen=(106.0, 68.0),
                    include_player_velocities=False, PlayerMarkerSize=10, PlayerAlpha=0.7):
    """ save_match_clip( hometeam, awayteam, fpath )
    
    Generates a movie from Metrica tracking data, saving it in the 'fpath' directory with name 'fname'
    
    Parameters
    -----------
        hometeam: home team tracking data DataFrame. Movie will be created from all rows in the DataFrame
        awayteam: away team tracking data DataFrame. The indices *must* match those of the hometeam DataFrame
        fpath: directory to save the movie
        fname: movie filename. Default is 'clip_test.mp4'
        fig,ax: Can be used to pass in the (fig,ax) objects of a previously generated pitch. Set to (fig,ax) to use an existing figure, or None (the default) to generate a new pitch plot,
        frames_per_second: frames per second to assume when generating the movie. Default is 25.
        team_colors: Tuple containing the team colors of the home & away team. Default is 'r' (red, home team) and 'b' (blue away team)
        field_dimen: tuple containing the length and width of the pitch in meters. Default is (106,68)
        include_player_velocities: Boolean variable that determines whether player velocities are also plotted (as quivers). Default is False
        PlayerMarkerSize: size of the individual player marlers. Default is 10
        PlayerAlpha: alpha (transparency) of player markers. Defaault is 0.7
        
    Returrns
    -----------
       fig,ax : figure and aixs objects (so that other data can be plotted onto the pitch)

    """
    # check that indices match first
    # assert np.all( hometeam.index==awayteam.index ), "Home and away team Dataframe indices must be the same"
    # in which case use home team index
    index = tracking_df.index
    # Set figure and movie settings
    FFMpegWriter = animation.writers['ffmpeg']
    metadata = dict(title='Tracking Data', artist='Matplotlib',
                    comment='Metrica tracking data clip')
    writer = FFMpegWriter(fps=frames_per_second, metadata=metadata)
    fname = fpath + '/' + fname + '.mp4'  # path and filename
    # create football pitch
    if figax is None:
        fig, ax = plot_pitch(field_dimen=field_dimen)
    else:
        fig, ax = figax
    fig.set_tight_layout(True)
    # Generate movie
    print("Generating movie...", end='')
    r = 0
    with writer.saving(fig, fname, 100):
        for i in index:
            figobjs = []  # this is used to collect up all the axis objects so that they can be deleted after each iteration
            cmap = 'bwr'
            objs = ax.imshow(np.flipud(PPCF[r]), extent=(
                -field_dimen[0] / 2., field_dimen[0] / 2., -field_dimen[1] / 2.,
                field_dimen[1] / 2.),
                             interpolation='spline36', vmin=0.0, vmax=1.0, cmap=cmap, alpha=0.5)
            figobjs.append(objs)
            for color, team_name in zip(team_colors, ['home', 'away']):
                team = tracking_df.loc[i]
                x_columns = [c for c in tracking_df.loc[i].keys() if c[-2:].lower() == '_x' and c[
                                                                                                :4] == team_name]  # column header for player x positions
                y_columns = [c for c in tracking_df.loc[i].keys() if c[-2:].lower() == '_y' and c[
                                                                                                :4] == team_name]  # column header for player y positions
                objs, = ax.plot(team[x_columns], team[y_columns], color + 'o',
                                MarkerSize=PlayerMarkerSize,
                                alpha=PlayerAlpha)  # plot player positions
                figobjs.append(objs)
                if include_player_velocities:
                    vx_columns = ['{}_vx'.format(c[:-2]) for c in
                                  x_columns]  # column header for player x positions
                    vy_columns = ['{}_vy'.format(c[:-2]) for c in
                                  y_columns]  # column header for player y positions
                    objs = ax.quiver(team[x_columns], team[y_columns], team[vx_columns],
                                     team[vy_columns], color=color, scale_units='inches', scale=1.,
                                     width=0.0015, headlength=5, headwidth=3, alpha=PlayerAlpha)
                    figobjs.append(objs)
            r = r + 1
            # plot ball
            objs, = ax.plot(team['ball_x'], team['ball_y'], 'ko', MarkerSize=6, alpha=1.0,
                            LineWidth=0)
            figobjs.append(objs)
            # include match time at the top
            frame_minute = int(team['time'] / 60.)
            frame_second = (team['time'] / 60. - frame_minute) * 60.
            timestring = "%d:%1.2f" % (frame_minute, frame_second)
            objs = ax.text(-2.5, field_dimen[1] / 2. + 1., timestring, fontsize=14)
            figobjs.append(objs)
            writer.grab_frame()
            # Delete all axis objects (other than pitch lines) in preperation for next frame
            for figobj in figobjs:
                figobj.remove()
    print("done")
    plt.clf()
    plt.close(fig)


def barplot_comparison(df_1, df_2, label1, label2, team='', show=True):
    bar_color = 'blue'
    bar_color_without = 'orange'

    # Set the style of the plot (optional)
    plt.style.use("seaborn-whitegrid")

    # Create an array of indices for the x-axis
    indices = np.arange(len(df_1))

    # Set the width of the bars
    bar_width = 0.35

    # Create a figure and axis for the bar plot
    plt.figure(figsize=(8, 6))

    # Create bars for home_df_velocities
    plt.bar(df_1['id'], df_1['PPCF'], bar_width, color=bar_color, label=f'{label1}')

    # Create bars for home_df_velocities_without, shift the indices to position them side by side
    plt.bar(indices + bar_width, df_2['PPCF'], bar_width, color=bar_color_without,
            label=f'{label2}')

    # Create a bar plot using Seaborn for home_df_velocities_without (orange color)

    # Set labels and title (optional)
    plt.xlabel("Player jersey", fontsize=18)  # Increase font size
    plt.ylabel("Player contribution", fontsize=18)  # Increase font size
    plt.title(f"Comparison of Player Contribution ({team})", fontsize=16)  # Increase font size
    plt.xticks(indices + bar_width / 2, df_1['id'], rotation=90, fontsize=12)  # Increase font size
    plt.yticks(fontsize=12)  # Increase font size

    # Add a legend to distinguish between 'With' and 'Without'
    plt.legend(fontsize=15)  # Increase font size

    # Increase border width
    for spine in plt.gca().spines.values():
        spine.set_linewidth(2.0)

    # Show the plot
    #plt.tight_layout()

    # Rotate the x-axis labels for better readability (optional)
    # plt.xticks(rotation=90)
    # plt.savefig("bar_plot.svg", transparent=True)  # Specify the desired file name and format
    # Show the plot
    if show:
        plt.show()
    return plt

def plot_velocity_vs_contribution(concatenated_df):
    plt.scatter(concatenated_df['percentil_90_vel'], concatenated_df['player_contribution'])
    plt.title('Speed vs player contribution')
    plt.xlabel('Speed (m/s)')
    plt.ylabel('Player contribution')
    plt.show()
