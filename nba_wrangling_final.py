# Stat 6021 Final Project Data Wrangling
# dylan greenleaf (djg3cg)

import numpy as np
import pandas as pd
import re

game_log = pd.read_csv("/Users/dylan/msds/linear models/Final Project/NBAgames_2014.csv")
game_log.describe
game_log.EVENTNUM[1] #All data looks to have been properly imported

shot_log = pd.read_csv("/Users/dylan/msds/linear models/Final Project/NBAshots_2014.csv")
shot_log.describe
shot_log.GAME_ID[1] #All data looks to have been properly imported

game_log.HOMEDESCRIPTION[1]
game_log.VISITORDESCRIPTION[1]

game_log["shot_or_not"] = np.nan # Initialize new column in shot log where we can store 1 or 0 based on shot taken

game_log.shot_or_not[7]
game_log.HOMEDESCRIPTION[7]
game_log.VISITORDESCRIPTION[7]

# test each observation to see if either description contains some reference to a shot being made
for i in range(0,len(game_log.shot_or_not)):
    if ('shot' in str(game_log.HOMEDESCRIPTION[i]).lower() or 'layup' in str(game_log.HOMEDESCRIPTION[i]).lower() or 'dunk' in str(game_log.HOMEDESCRIPTION[i]).lower()
        or 'shot' in str(game_log.VISITORDESCRIPTION[i]).lower() or 'layup' in str(game_log.VISITORDESCRIPTION[i]).lower() or 'dunk' in str(game_log.VISITORDESCRIPTION[i]).lower()):
        game_log.loc[i,'shot_or_not'] = 1
    else:
        game_log.loc[i,'shot_or_not'] = 0
        
# write partially cleaned data set to file just in case program crashes
game_log.to_csv("/Users/dylan/msds/linear models/Final Project/NBAgames_2014_cleaning.csv", index = False)


# create data frame containing only the shot log observations pertaining to a field goal
game_log_shots_only = game_log[game_log['shot_or_not'] > 0]
game_log_shots_only.describe # we need to reset the index values
game_log_shots_only.reset_index(inplace = True)
game_log_shots_only.to_csv("/Users/dylan/msds/linear models/Final Project/NBAgames_2014_just_shots.csv", index = False)

game_log_shots_only = pd.read_csv("/Users/dylan/msds/linear models/Final Project/NBAgames_2014_just_shots.csv")
shot_log = pd.read_csv("/Users/dylan/msds/linear models/Final Project/NBAshots_2014_2.csv")

# convert game clock values to seconds for shot log
for i in range(0,len(shot_log.GAME_CLOCK)):
    time = re.split(':', shot_log.loc[i,'GAME_CLOCK'])
    shot_log.loc[i,'GAME_CLOCK'] = int(time[0])*60 + int(time[1])

# convert game clock values to seconds for game log shot observations
for i in range(0,len(game_log_shots_only.PCTIMESTRING)):
    time = re.split(':', game_log_shots_only.PCTIMESTRING[i])
    game_log_shots_only.loc[i,'PCTIMESTRING'] = int(time[0])*60 + int(time[1])
    
# convert game clock values to seconds for entire game log
for i in range(0,len(game_log.PCTIMESTRING)):
    time = re.split(':', game_log.PCTIMESTRING[i])
    game_log.loc[i,'PCTIMESTRING'] = int(time[0])*60 + int(time[1])

# use game clock second values calculated above along with the period for each observation
# to compute a new variable indicating home many seconds are left in the game
shot_log['Time_left'] = (48-12*shot_log.PERIOD)*60 + shot_log.GAME_CLOCK
game_log_shots_only['Time_left'] = (48-12*game_log_shots_only.PERIOD)*60 + game_log_shots_only.PCTIMESTRING
game_log['Time_left'] = (48-12*game_log.PERIOD)*60 + game_log.PCTIMESTRING


# as it stands, the timeleft is off for corresponding observations of the 2 data frames by a few seconds
# take the gamelog times left as a reference and set the shotlog times left as the gamelog time that is
# closest to each time.

game_log_shots_only = pd.read_csv("/Users/dylan/msds/linear models/Final Project/NBAgames_2014_just_shots.csv")
shot_log = pd.read_csv("/Users/dylan/msds/linear models/Final Project/NBAshots_2014_2.csv")

# Create list of set of all game IDs from 2014
games = shot_log.GAME_ID.unique()  
game_count = 0
shot_count = 0

# The .loc method fails the first times it's called in the code, so I'm running it here with a dummy variable
shot_log_dummy = shot_log[shot_log.GAME_ID == games[0]]
shot_log_dummy.loc[game_count,'Time_left'] = 0
shot_log_dummy.loc[game_count,'Time_left'] = 0

# Adjust code below to find index of minimum time returned. Then  we can check to see if the player ID
# in the gamelog corresponding to that index is the same as player ID for the shot being considered

for game in games:
    #print(game)    
    shot_count = 0
    game_log_dummy = game_log_shots_only[game_log_shots_only.GAME_ID == game]
    shot_log_dummy = shot_log[shot_log.GAME_ID == game] 
    shot_log_dummy = shot_log_dummy.reset_index(drop=True)
    shot_log_dummy2 = shot_log[shot_log.GAME_ID == game]
    shot_log_dummy2 = shot_log_dummy2.reset_index(drop=True)
    while (len(shot_log_dummy) > 1):
        gl_times = game_log_dummy.Time_left
        close_time = min(gl_times, key=lambda x:abs(x-shot_log_dummy.Time_left.iloc[0]))
        index = game_log_dummy[game_log_dummy['Time_left'] == close_time].index[0]
        if (game_log_dummy.loc[index,'PLAYER1_ID'] == shot_log_dummy.PlayerID.iloc[0] and shot_log_dummy.PTS.iloc[0] > 0 and game_log_dummy.loc[index,'shot_or_not'] == 1):
            if('pts' in str(game_log_dummy.loc[index,'HOMEDESCRIPTION']).lower() or 'pts' in str(game_log_dummy.loc[index,'VISITORDESCRIPTION']).lower()): 
                shot_log_dummy2.loc[shot_count,'Time_left'] = close_time
        elif (game_log_dummy.loc[index,'PLAYER1_ID'] == shot_log_dummy.PlayerID.iloc[0] and shot_log_dummy.PTS.iloc[0] == 0 and game_log_dummy.loc[index,'shot_or_not'] == 1):
            if('pts' not in str(game_log_dummy.loc[index,'HOMEDESCRIPTION']).lower() and 'pts' not in str(game_log_dummy.loc[index,'VISITORDESCRIPTION']).lower()): 
                shot_log_dummy2.loc[shot_count,'Time_left'] = close_time  
                        
        else:
            close_time = sorted(gl_times, key=lambda x:abs(x-shot_log_dummy.Time_left.iloc[0]))[1]
            index = game_log_dummy[game_log_dummy['Time_left'] == close_time].index[0]            
            if (game_log_dummy.loc[index,'PLAYER1_ID'] == shot_log_dummy.PlayerID.iloc[0] and shot_log_dummy.PTS.iloc[0] > 0 and game_log_dummy.loc[index,'shot_or_not'] == 1):
                if('pts' in str(game_log_dummy.loc[index,'HOMEDESCRIPTION']).lower() or 'pts' in str(game_log_dummy.loc[index,'VISITORDESCRIPTION']).lower()):                 
                    shot_log_dummy2.loc[shot_count,'Time_left'] = close_time
            elif (game_log_dummy.loc[index,'PLAYER1_ID'] == shot_log_dummy.PlayerID.iloc[0] and shot_log_dummy.PTS.iloc[0] == 0 and game_log_dummy.loc[index,'shot_or_not'] == 1):
                if('pts' not in str(game_log_dummy.loc[index,'HOMEDESCRIPTION']).lower() and 'pts' not in str(game_log_dummy.loc[index,'VISITORDESCRIPTION']).lower()):
                    shot_log_dummy2.loc[shot_count,'Time_left'] = close_time   
            
            else:
                close_time = sorted(gl_times, key=lambda x:abs(x-shot_log_dummy.Time_left.iloc[0]))[2]
                index = game_log_dummy[game_log_dummy['Time_left'] == close_time].index[0]
                if (game_log_dummy.loc[index,'PLAYER1_ID'] == shot_log_dummy.PlayerID.iloc[0] and shot_log_dummy.PTS.iloc[0] > 0 and game_log_dummy.loc[index,'shot_or_not'] == 1):
                    if('pts' in str(game_log_dummy.loc[index,'HOMEDESCRIPTION']).lower() or 'pts' in str(game_log_dummy.loc[index,'VISITORDESCRIPTION']).lower()):                 
                        shot_log_dummy2.loc[shot_count,'Time_left'] = close_time
                elif (game_log_dummy.loc[index,'PLAYER1_ID'] == shot_log_dummy.PlayerID.iloc[0] and shot_log_dummy.PTS.iloc[0] == 0 and game_log_dummy.loc[index,'shot_or_not'] == 1):
                    if('pts' not in str(game_log_dummy.loc[index,'HOMEDESCRIPTION']).lower() and 'pts' not in str(game_log_dummy.loc[index,'VISITORDESCRIPTION']).lower()):
                        shot_log_dummy2.loc[shot_count,'Time_left'] = close_time
                        
                else:
                    close_time = sorted(gl_times, key=lambda x:abs(x-shot_log_dummy.Time_left.iloc[0]))[3]
                    index = game_log_dummy[game_log_dummy['Time_left'] == close_time].index[0]
                    if (game_log_dummy.loc[index,'PLAYER1_ID'] == shot_log_dummy.PlayerID.iloc[0] and shot_log_dummy.PTS.iloc[0] > 0 and game_log_dummy.loc[index,'shot_or_not'] == 1):
                        if('pts' in str(game_log_dummy.loc[index,'HOMEDESCRIPTION']).lower() or 'pts' in str(game_log_dummy.loc[index,'VISITORDESCRIPTION']).lower()):                 
                            shot_log_dummy2.loc[shot_count,'Time_left'] = close_time
                    elif (game_log_dummy.loc[index,'PLAYER1_ID'] == shot_log_dummy.PlayerID.iloc[0] and shot_log_dummy.PTS.iloc[0] == 0 and game_log_dummy.loc[index,'shot_or_not'] == 1):
                        if('pts' not in str(game_log_dummy.loc[index,'HOMEDESCRIPTION']).lower() and 'pts' not in str(game_log_dummy.loc[index,'VISITORDESCRIPTION']).lower()):
                            shot_log_dummy2.loc[shot_count,'Time_left'] = close_time   
        
        shot_log_dummy = shot_log_dummy.drop(shot_log_dummy.index[0]) 
        shot_count += 1
        #print(shot_count)
        
    if(game_count == 0):
        new_shot_log = shot_log_dummy2
    elif (game_count > 0):
        new_shot_log = pd.concat([new_shot_log,shot_log_dummy2])            
    game_count += 1
    print(game_count)




# add in a shot_or_not variable so that shots don't incorrectly join on other events
new_shot_log['shot_or_not'] = 1


# left outer join data sets (game_log on left) on the columns for GAME_ID, Time_left, PlayerID, and shot_or_not

new_game_log = pd.merge(game_log, new_shot_log, how='left', on=['GAME_ID', 'Time_left','PlayerID','shot_or_not'], sort=False)
   
 
new_game_log.to_csv("C:/Users/brian/Documents/UVA/Linear Models/Final Project/NBA_2014_combined.csv", index = False)
      
      

###################################################################################################
#
# Add in last year's FG % for player taking the shot, and FG % allowed for the closest defender
#
###################################################################################################

merged_game_log = pd.read_csv("C:/Users/brian/Documents/UVA/Linear Models/Final Project/NBA_2014_combined.csv")
shots_2013 = pd.read_csv("C:/Users/brian/Documents/UVA/Linear Models/Final Project/NBAshots_2013.csv")


shot_attempts = pd.DataFrame(shots_2013.groupby('PlayerID')['FGM'].count())
shot_attempts['PlayerID'] = shot_attempts.index

shot_made = pd.DataFrame(shots_2013.groupby('PlayerID')['FGM'].sum())
shot_made['PlayerID'] = shot_made.index

total_FGperc = pd.merge(shot_attempts, shot_made, how='left', on=['PlayerID'], sort=False)
total_FGperc['FGperc'] = total_FGperc['FGM_y']/total_FGperc['FGM_x']

total_FGperc['shot_or_not'] = 1


merged_game_log = pd.merge(merged_game_log, total_FGperc, how='left', on=['PlayerID','shot_or_not'], sort=False)

######################################################################################

def_shot_attempts = pd.DataFrame(shots_2013.groupby('CLOSEST_DEFENDER_PLAYER_ID')['FGM'].count())
def_shot_attempts['CLOSEST_DEFENDER_PLAYER_ID'] = def_shot_attempts.index

def_shot_made = pd.DataFrame(shots_2013.groupby('CLOSEST_DEFENDER_PLAYER_ID')['FGM'].sum())
def_shot_made['CLOSEST_DEFENDER_PLAYER_ID'] = def_shot_made.index

def_total_FGperc = pd.merge(def_shot_attempts, def_shot_made, how='left', on=['CLOSEST_DEFENDER_PLAYER_ID'], sort=False)
def_total_FGperc['DefFGperc'] = def_total_FGperc['FGM_y']/def_total_FGperc['FGM_x']

def_total_FGperc['shot_or_not'] = 1


merged_game_log = pd.merge(merged_game_log, def_total_FGperc, how='left', on=['CLOSEST_DEFENDER_PLAYER_ID','shot_or_not'], sort=False)

merged_game_log.to_csv("C:/Users/brian/Documents/UVA/Linear Models/Final Project/NBA_2014_combined_FGperc.csv", index = False)





#########################################################################################
# Below is the code to add time_in_game variable after data set has been further modified.

import numpy as np
import pandas as pd
import re
import math

master = pd.read_csv("/Users/dylan/msds/linear models/Final Project/NBA_2014_combined_FGperc_withposition_subs.csv")

# Create list of set of all game IDs from 2014
games = list(master.GAME_ID.unique())
games = games[0:10]


#game = games[0]

#master = master[master['GAME_ID'].isin(games)]
# Create new variable time_sub and initialize it to NA
master['time_sub'] = np.NaN


for game in games:
    print(game)
    game_events = master[master['GAME_ID'] == game]
    players = list(master[master['GAME_ID'] == game].PlayerID.unique())
    for player in players:
        #print(player)
        events1 = game_events[game_events['PlayerID'] == player]
        events1 = events1[events1['Time_left'] >= 1440]        
        events2 = game_events[game_events['PlayerID'] == player]
        events2 = events2[events2['Time_left'] < 1440]
        indices1 = events1.index.get_values()
        indices2 = events2.index.get_values()
        for i in range(0, len(events1)):
            index = indices1[i]
            if (events1.shot_or_not[index] == 0):
                continue
            else:
                sub_i = np.NaN
                if(len(events1[events1['SUBIN'] == player])>0):
                    sub_i = events1[events1['SUBIN'] == player]
                    sub_i = sub_i[sub_i['SUBIN'].index < i]
                    sub_i = sorted(sub_i, reverse = True)[0]
                if (np.isnan(sub_i) != True):
                    master.loc[index, 'time_sub'] = events1.loc[sub_i, 'Time_left'] - events1.loc[index, 'Time_left']
                else:
                    master.loc[index, 'time_sub'] = 2880 - events1.loc[index, 'Time_left']
                    
        for i in range(0, len(events2)):
            index = indices2[i]
            if (events2.shot_or_not[index] == 0):
                continue
            else:
                sub_i = np.NaN
                if(len(events2[events2['SUBIN'] == player])>0):
                    sub_i = events2[events2['SUBIN'] == player]
                    sub_i = sub_i[sub_i['SUBIN'].index < index]
                    sub_i = sorted(sub_i, reverse = True)[0]
                if (np.isnan(sub_i) != True):
                    master.loc[index, 'time_sub'] = events2.loc[sub_i, 'Time_left'] - events2.loc[index, 'Time_left']
                else:
                    master.loc[index, 'time_sub'] = 1440 - events2.loc[index, 'Time_left']
                    

# Fill in missing scoremargin values with previous score
master['SCOREMARGIN'] = master['SCOREMARGIN'].fillna(method = 'ffill')

# Flip the margin values for the away team so each margin shows how much the team shooting is down
for i in range(0,len(master)):
    if (master.loc[i,'LOCATION'] == 'A'):
        if (master.loc[i, 'SCOREMARGIN'] == 'TIE'):
            break
        elif np.isnan(int(master.loc[i, 'SCOREMARGIN'])):
            break
        else:
            master.loc[i, 'SCOREMARGIN'] = -(int(master.loc[i,'SCOREMARGIN']))                



# Export master to csv file
master.to_csv("/Users/dylan/msds/linear models/Final Project/NBA_2014_Final_Combined", index = False)     
      
            


      
      
      
