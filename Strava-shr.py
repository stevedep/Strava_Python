#!/usr/bin/env python
# coding: utf-8

# In[1]:


#AUTHORIZE

#https://medium.com/swlh/using-python-to-connect-to-stravas-api-and-analyse-your-activities-dummies-guide-5f49727aac86
#http://www.strava.com/oauth/authorize?client_id=01234&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=read,activity:read_all,activity:write

import requests
import json
# Make Strava auth API call with your 
# client_code, client_secret and code
response = requests.post(
                    url = 'https://www.strava.com/oauth/token',
                    data = {
                            'client_id': 01234,
                            'client_secret': '---',
                            'code': '---',
                            'grant_type': 'authorization_code'
                            }
                )
#Save json response as a variable
strava_tokens = response.json()
# Save tokens to file
with open('strava_tokens.json', 'w') as outfile:
    json.dump(strava_tokens, outfile)
# Open JSON file and print the file contents 
# to check it's worked properly
with open('strava_tokens.json') as check:
  data = json.load(check)
print(data)

#refresh token
def refresh_token():
    import requests
    import json
    import time

    # Get the tokens from file to connect to Strava
    with open('strava_tokens.json') as json_file:
        strava_tokens = json.load(json_file)
    # If access_token has expired then 
    # use the refresh_token to get the new access_token
    if strava_tokens['expires_at'] < time.time():
    # Make Strava auth API call with current refresh token
        print('token refreshed')
        response = requests.post(
                            url = 'https://www.strava.com/oauth/token',
                            data = {
                                    'client_id': 01234,
                                    'client_secret': '---',
                                    'grant_type': 'refresh_token',
                                    'refresh_token': strava_tokens['refresh_token']
                                    }
                        )
    # Save response as json in new variable
        new_strava_tokens = response.json()
    # Save new tokens to file
        with open('strava_tokens.json', 'w') as outfile:
            json.dump(new_strava_tokens, outfile)
    # Use new Strava tokens from now
        strava_tokens = new_strava_tokens
    # Open the new JSON file and print the file contents 
    # to check it's worked properly
    with open('strava_tokens.json') as check:
      data = json.load(check)
    print(data)

def get_activitydata(idpar):
    url = "https://www.strava.com/api/v3/activities/" + str(idpar) + "/streams/time"
    r = requests.get(url + '?access_token=' + access_token + '&types=["time"]&key_by_type=true')
    r = r.json()
    return r

def create_dataframe(r):
    df = pd.DataFrame(r['distance']['data'])
    df2 = pd.DataFrame(r['time']['data'])
    df3= pd.concat([df, df2], axis=1)
    df_res = pd.concat([df3.shift(1), df3], axis=1)
    df_res.columns = ['dist-1', 'time-1', 'dist', 'time']
    df_res['time_diff'] = df_res['time'] - df_res['time-1']
    df_res['dist_diff'] = df_res['dist'] - df_res['dist-1']
    df_res['speed'] = (df_res['dist_diff'] / df_res['time_diff']) * 3.6
    df_res['sumcumtimediff'] =  df_res.sort_values(by=['speed'], ascending=True)['time_diff'].cumsum()
    df_res['sumcumdistdiff'] =  df_res.sort_values(by=['speed'], ascending=True)['dist_diff'].cumsum()
    time = df_res.loc[df_res['speed'].size-1]['time']
    df_res['percentile'] = (df_res['sumcumtimediff']) / time 
    df_res['percentilerounded'] = round((df_res['percentile'] * 100) , 0) 
    return df_res

def calculate_split(df_res, minutes):
    lst = []
    #minutes = 20
    interval = minutes * 60

    for index, row in df_res.iterrows():    
        if df_res[df_res['time']<=row['time']-interval]['time'].size != 0:
            val = max(df_res[df_res['time']<=row['time']-interval]['time'])
            record = df_res[df_res['time']==val]
            timediff = row['time'] - record['time']
            distdiff = row['dist'] - record['dist']
            speed = (distdiff / timediff) * 3.6
            #print(str(row['time']) + " avg speed " + str(speed.to_string(index=False)))
            lst.append(float(speed.to_string(index=False)))
        else:
            lst.append(0)
    
    
    val = max(lst)
    p = lst.index(val)
    df2 = df_res.filter(items = [p], axis=0)
    
    timeval = max(df_res[df_res['time']<=int(float((df2['time']-(60*minutes)).to_string(index=False)))]['time'])
    kmrecord = df_res[df_res['time']==timeval]
    #print(int(float((df2['time']-(60*minutes)).to_string(index=False))))
    
    
    return [str(round(val,2)), str(int(float(((df2['time']/60)-minutes).to_string(index=False)))),
           str(round(float(((kmrecord['dist']/1000)).to_string(index=False)),2))]

def update_post(idpar, datapar):
    endpoint = "https://www.strava.com/api/v3/activities/" + str(idpar)
    data = datapar
    headers = {"Authorization": "Bearer " + access_token}

    requests.put(endpoint, data=data, headers=headers).json()
    print('updated')

def update_activity_post(idpar, distpar, timepar):
    r = get_activitydata(idpar)
    
    if list(r.keys())[0] == 'distance':
        df_res = create_dataframe(r)

        if max(df_res['time']) / 60 > 10:
            result_10 = calculate_split(df_res, 10)
        else:
            result_10 = ['0', '0', '0']
        if max(df_res['time']) / 60 > 20:
            result_20 = calculate_split(df_res, 20)
        else:
            result_20 = ['0', '0', '0']
        if max(df_res['time']) / 60 > 30:
            result_30 = calculate_split(df_res, 30)
        else:
            result_30 = ['0', '0', '0']

        subset = df_res[df_res['speed']<=20]

        maxtimediff = max(subset['sumcumtimediff'])

        maxdistdiff = max(subset['sumcumdistdiff']) 
        
        movingspeed = round((((distpar - maxdistdiff) / (timepar - maxtimediff)) * 3.6),2)
        
        timemoving = round(((timepar - maxtimediff) / 60),0)
        
        prctimemoving = round((((timepar - maxtimediff) / timepar) * 100),0)
        
        data = {
            'description': 'Avg. Moving speed (20+): ' + str(movingspeed) + ' (' + str(prctimemoving) + '%, ' + str(timemoving) + ' mins )' + '''
50% Qrt Speed: ''' + str(round(min(df_res[df_res['percentilerounded']==50]['speed']),2)) + '''
Best 10 min Speed: ''' + result_10[0] + ' @ ' + result_10[1] + ' min & ' + result_10[2] + ' km.' + '''
Best 20 min Speed: ''' + result_20[0] + ' @ ' + result_20[1] + ' min & ' + result_20[2] + ' km.' + '''
Best 30 min Speed: ''' + result_30[0] + ' @ ' + result_30[1] + ' min & ' + result_30[2] + ' km.' + '''
75% Qrt Speed: ''' + str(round(min(df_res[df_res['percentilerounded']==75]['speed']),2))
                }

        update_post(idpar, data)
    

#GET ACTIVITIES

import requests
import pandas as pd
from pandas.io.json import json_normalize
import json
import csv
refresh_token()
# Get the tokens from file to connect to Strava
with open('strava_tokens.json') as json_file:
    strava_tokens = json.load(json_file)
# Loop through all activities
url = "https://www.strava.com/api/v3/activities"
access_token = strava_tokens['access_token']
# Get first page of activities from Strava with all fields
r = requests.get(url + '?access_token=' + access_token)
r = r.json()
    
df = pd.json_normalize(r)
#df.to_csv('strava_activities_all_fields.csv')
df.head(n=20)

for index, acrow in df.head(n=2).iterrows():
    print(acrow['id'])
    if acrow['distance'] > 2000 and acrow['type'] == 'Ride':  
        update_activity_post(acrow['id'], acrow['distance'], acrow['elapsed_time'] )

