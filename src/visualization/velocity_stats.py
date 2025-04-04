import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import cm
import joypy


def compare_velocity_teams(df, opacity=0.6):
    """Velocity density plot of each team"""
    # Create a figure and axis object
    fig, ax = plt.subplots()

    # Create a density plot for each team using seaborn
    for team, color in zip(df['team'].unique(),
                           sns.color_palette('husl', n_colors=len(df['team'].unique()))):
        team_data = df[df['team'] == team]['velocity']
        sns.kdeplot(team_data, ax=ax, label=f'Team {team}', color=color, alpha=opacity)

    # Add labels and a legend
    ax.set_xlabel('Velocity')
    ax.set_ylabel('Density')
    ax.set_title('Velocity Density Plot by Team')
    ax.legend()

    return fig, ax


def joyplot_team(df, team='home', max_velocity=6):
    """Velocity joyploy of each team"""
    df = df[(df['team'] == team) & (df['velocity'] < max_velocity)]

    fig, ax = joypy.joyplot(df, by='jersey', column='velocity', colormap=cm.summer,
                            title=f'Velocity profile of {team}', kind="counts")
    return fig, ax
