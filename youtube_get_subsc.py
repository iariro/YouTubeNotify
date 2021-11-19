#!/usr/bin/python3

import ambient
from googleapiclient.discovery import build

YOUTUBE_API_KEY = 'AIzaSyBuV44B4RZq90SnDs_GvCz7zXwrR34ixXI'

channels = ['UCVD_BTWC0dmWPZOWagpEeiA', # 'k k': 
            'UC402okxWzbtUDIjKD4EQBsQ', # 'Ken Drumschool': 
            'UCzTC_3yTbvyZLkUp1FxdMDA'] # 'rocky music': 

def youtube_channel_detail(channel_id, api_key):
    api_service_name = 'youtube'
    api_version = 'v3'
    youtube = build(api_service_name, api_version, developerKey=api_key)
    search_response = youtube.channels().list(
        part='snippet,statistics',
        id=channel_id,
    ).execute()

    return search_response['items'][0]


if __name__ == '__main__':
    cnts = {}
    ambi = ambient.Ambient(44031, 'e857a6cd408e29b5')
    for i, channel_id in enumerate(channels):
        d = youtube_channel_detail(channel_id, YOUTUBE_API_KEY)
        cnts['d{}'.format(i + 1)] = d['statistics']['subscriberCount']
    ambi.send(cnts)
