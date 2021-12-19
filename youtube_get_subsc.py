#!/usr/bin/python3

import csv
import ambient
from googleapiclient.discovery import build

YOUTUBE_API_KEY = 'AIzaSyBuV44B4RZq90SnDs_GvCz7zXwrR34ixXI'

def youtube_channel_detail(channel_id, api_key):
    api_service_name = 'youtube'
    api_version = 'v3'
    youtube = build(api_service_name, api_version, developerKey=api_key)
    search_response = youtube.channels().list(
        part='snippet,statistics',
        id=channel_id,
    ).execute()

    return search_response['items'][0]

def read_channels_from_csv(file_path):
    channels = []
    with open(file_path) as f:
        reader = csv.reader(f)
        for row in reader:
            channels.append(row[0])

    return channels

if __name__ == '__main__':
    cnts = {}
    ambi = ambient.Ambient(44031, 'e857a6cd408e29b5')
    channels = read_channels_from_csv('/home/pi/doc/private/python/youtube/youtube_get_subsc_list.txt')
    for i, channel_id in enumerate(channels):
        d = youtube_channel_detail(channel_id, YOUTUBE_API_KEY)
        cnts['d{}'.format(i + 1)] = d['statistics']['subscriberCount']
    ambi.send(cnts)
