#!/usr/bin/env python
# coding: utf-8

# In[1]:


from googleapiclient.discovery import build
from dateutil import parser
from datetime import datetime 
import pandas as pd
import numpy as np
from IPython.display import JSON

# Import data visualization package
import seaborn as sns
import matplotlib.pyplot as plt

#NLP
from wordcloud import WordCloud


# In[2]:


api_key = 'AIzaSyCk1DRU59grPDuxFACX5y3YmRDNNRa9ZcQ'


# In[3]:


channel_ids = ['UCxJGMJbjokfnr2-s4_RXPxQ' , 
               # more channels here
              ]


# In[4]:


api_service_name = "youtube"
api_version = "v3"

# Get credentials and create an API client
youtube = build(
    api_service_name, api_version, developerKey=api_key)


# In[5]:


def get_channel_stats(youtube, channel_ids):
    all_data = []

    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=','.join(channel_ids)
    )
    response = request.execute()

    # loop through items
    for item in response['items']:
        data = {'channelName': item['snippet']['title'],
                'subscribers': item['statistics']['subscriberCount'],
                'views': item['statistics']['viewCount'],
                'totalVideos': item['statistics']['videoCount'],
                'playlistId': item['contentDetails']['relatedPlaylists']['uploads']
        }

        all_data.append(data)

    return(pd.DataFrame(all_data))


# In[6]:


channel_stats = get_channel_stats(youtube, channel_ids)


# In[7]:


channel_stats


# In[8]:


playlist_id = "UUxJGMJbjokfnr2-s4_RXPxQ"

def get_video_ids(youtube, playlist_id):

    video_ids = []

    request = youtube.playlistItems().list(
        part = "snippet,contentDetails",
        maxResults = 50,
        playlistId = playlist_id
    )
    response = request.execute()
    
    for item in response['items']:
        video_ids.append(item['contentDetails']['videoId'])
        
    next_page_token = response.get('nextPageToken')
    while next_page_token is not None: 
        request = youtube.playlistItems().list(
                part = "contentDetails",
                maxResults = 50,
                playlistId = playlist_id,
                pageToken = next_page_token)
    
        response = request.execute()
        
        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])
            
        next_page_token = response.get('nextPageToken')
    
    return video_ids


# In[9]:


video_ids = get_video_ids (youtube, playlist_id)


# In[10]:


len(video_ids)


# In[11]:


def get_video_details(youtube,video_ids):
                       
    all_video_info = []
    
    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(video_ids[i:i+50])
        )

        response = request.execute()

        for video in response['items']:
            video_stats = {'snippet' : ['channelTitle', 'title', 'description', 'tags', 'publishedAt'],
                           'statistics' : ['viewCount', 'likeCount', 'favoriteCount', 'commentCount'],
                           'contentDetails' : ['duration', 'definition', 'caption']
                          }

            video_info = {}
            video_info['video_id'] = video['id']

            for k in video_stats.keys():
                for v in video_stats[k]:
                    try: 
                        video_info[v] = video[k][v]
                    except:
                        video_info[v] = None

            all_video_info.append(video_info)
            
        return pd.DataFrame(all_video_info)
    


# In[12]:


video_df_original = get_video_details(youtube,video_ids)
video_df_original.head()


# In[13]:


video_df = video_df_original.copy(deep = True) #default = true 


# ### Data pre-processing

# In[14]:


#Checking null value 

video_df.isnull().any()


# In[15]:


video_df.dtypes


# In[16]:


numeric_cols = ['viewCount', 'likeCount', 'favoriteCount', 'commentCount']
video_df[numeric_cols] = video_df[numeric_cols].apply(pd.to_numeric, axis = 1)


# In[17]:


video_df.dtypes


# In[18]:


#publish day in the week
video_df['publishedAt'] = video_df['publishedAt'].apply(lambda x: parser.parse(x)) 


# In[19]:


video_df['publishDayName'] = video_df['publishedAt'].apply(lambda x: x.strftime("%A"))


# In[20]:


video_df['publishDayName'].head()


# In[21]:


# convert duration to seconds 
import isodate
video_df['durationSecs'] = video_df['duration'].apply(lambda x: isodate.parse_duration(x))
video_df['durationSecs'] = video_df['durationSecs'].astype('timedelta64[s]')


# In[22]:


video_df[['durationSecs','duration']].head()


# In[23]:


# add tag count
video_df['tagCount'] = video_df['tags'].apply(lambda x: 0 if x is None else len(x))


# In[24]:


video_df[['tagCount','title']].head()


# ### EDA

# ### Top 10 best performance videos 

# In[25]:


ax = sns.barplot(x = 'title', y = 'viewCount', data = video_df.sort_values('viewCount', ascending = False)[0:11])
plot = ax.set_xticklabels(ax.get_xticklabels(), rotation=90)


# ### 10 worst performance videos 

# In[26]:


ax = sns.barplot(x = 'title', y = 'viewCount', data = video_df.sort_values('viewCount', ascending = True)[0:11])
plot = ax.set_xticklabels(ax.get_xticklabels(), rotation=90)


# ### View distribution per video

# In[27]:


sns.violinplot(x = video_df['channelTitle'], y = video_df['viewCount'])


# ### Views vs Like and Comments

# In[28]:


fig, ax = plt.subplots(1, 2, figsize=(10, 8))
ax1 = sns.scatterplot(data = video_df, x = "commentCount", y = "viewCount", ax = ax[0])
ax2 = sns.scatterplot(data = video_df, x = "likeCount", y = "viewCount", ax = ax[1])
fig.tight_layout(pad = 5)


# ### Video Duration

# In[29]:


sns.histplot(data=video_df, x='durationSecs', bins = 30)
plt.figure(figsize=(30,20))


# ### Video Duration vs Views

# In[33]:


sns.scatterplot(data=video_df, x="durationSecs", y="viewCount")


# In[36]:


video_df['durationSecs'].corr(video_df['viewCount'])


# ### Published Date vs Views

# In[39]:


sns.barplot(data = video_df, x="publishDayName", y="viewCount")


# In[42]:


pd.crosstab(index=video_df['publishDayName'], columns='count')


# ### Number of tags vs views

# In[44]:


sns.scatterplot(data=video_df, x="tagCount", y="viewCount")


# In[45]:


video_df['tagCount'].corr(video_df['viewCount'])

