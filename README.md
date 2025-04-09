# Pitch Control
This code computes the pitch control contribution contribution of each player of both teams in each of the three zones of the pitch (defensive, middle, and attacking). The code is based on [LarieOnTracking](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking), which is the implementation of the model presented in [1].

# Data
The data used in this code is the tracking data of a football match obtained with Tracab Optical Tracking System. The data used is not publicly available, but the code can be used with any tracking data that has the same format as the one used in the code. The data should be in a CSV file where each player should have a unique ID and two position columns (home_n_x, home_n_y, away_n_x, away_n_y) for each player. The data should also have a time column (time), two ball positions columns, one indicating if the ball is in play or not and one indicating the possession of the ball (home, away). A dummy example can be found in the data/processed folder.

# How to execute code

The code can be executed in multiple ways, you need to add the name of the traking file you want to analyze and the number of frames between pitch control computation.
Then you can run it with individual velocities (-iv), with stamina factor applied to home team or/and away team (sh/sa) and there is also the possibility to apply the stamina factor to a certain position (defenders, midfielders, strikers).

## Some examples of how to run the code:
```bash
   python main.py Aclean1_1074815 -o 25
   python main.py Aclean1_1074815 -o 25 -iv
   python main.py Aclean1_1074815 -o 25 -iv -sh 1.2
   python main.py Aclean1_1074815 -o 25 -iv -sh 1.2 -sa 1.2 -pos Defenders
   ```

# References
[1] Spearman, W., Basye, A., Dick, G., Hotovy, R., & Pop, P. (2017, March). Physics-based modeling of pass probabilities in soccer. In Proceeding of the 11th MIT Sloan Sports Analytics Conference (Vol. 1).





