#!/usr/bin/python3

# -*- coding: utf-8 -*-

import re
import os
import sys
import json
import datetime
import googleapiclient.discovery
import requests
import unicodedata

api_service_name = "youtube"
api_version = "v3"


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_authenticated_service(developerKey):
    return googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=developerKey)


def get_uploads_playlist_id(youtube, channel_id):
    request = youtube.channels().list(
        part="contentDetails",
        id=channel_id,
        fields="items/contentDetails/relatedPlaylists/uploads"
    )
    response = request.execute()
    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_video_id_in_playlist(youtube, playlistId):
    video_id_list = []

    request = youtube.playlistItems().list(
        part="snippet",
        maxResults=50,
        playlistId=playlistId,
        fields="nextPageToken,items/snippet/resourceId/videoId"
    )

    while request:
        response = request.execute()
        video_id_list.extend([item["snippet"]["resourceId"]["videoId"] for item in response["items"]])
        request = youtube.playlistItems().list_next(request, response)

    return video_id_list


def get_video_items(youtube, video_id_list):
    video_items = []

    chunk_list = list(chunks(video_id_list, 50))  # max 50 id per request.
    for chunk in chunk_list:
        video_ids = ",".join(chunk)
        request = youtube.videos().list(
            part="snippet,statistics",
            id=video_ids,
            fields="items(id,snippet(title,description,publishedAt,thumbnails),statistics(viewCount,likeCount))")
        response = request.execute()
        video_items.extend(response["items"])

    return {item["id"]: {
            'title': item["snippet"]["title"],
            'publishedAt': item["snippet"]["publishedAt"],
            'views': int(item["statistics"]["viewCount"]),
            'likes': int(item["statistics"]["likeCount"])} for item in video_items}


def like_count_diff(json_file, channel_id, regular, adjust_sonant_mark):
    video_items_old = None
    if os.path.isfile(json_file):
        with open(json_file, 'r') as f:
            video_items_old = json.load(f)

    youtube = get_authenticated_service('AIzaSyBuV44B4RZq90SnDs_GvCz7zXwrR34ixXI')
    uploads_playlist_id = get_uploads_playlist_id(youtube, channel_id)
    video_id_list = get_video_id_in_playlist(youtube, uploads_playlist_id)
    video_items = get_video_items(youtube, video_id_list)

    if regular:
        with open(json_file, 'w') as f:
            json.dump(video_items, f, indent=4, ensure_ascii=False)

    diff_likes = []
    diff_views = []
    if video_items_old:
        view_total = 0
        like_total = 0
        video_id_sorted = sorted(video_items.items(), key=lambda x: x[1]['publishedAt'], reverse=True)
        for video_id, item in video_id_sorted:
            title = video_items[video_id]['title']
            likes_new = video_items[video_id]['likes']
            views_new = video_items[video_id]['views']
            if video_id in video_items_old:
                likes_old = video_items_old[video_id]['likes']
                views_old = video_items_old[video_id]['views']
                m = re.match(r'(.*)を演奏.*', title)
                if m:
                    title = m.group(1)
                else:
                    m = re.match(r'(.*)とか演奏.*', title)
                    if m:
                        title = m.group(1)

                if likes_new != likes_old:
                    like_total += likes_new - likes_old
                    diff_likes.append('{}：{}→{}({})'.format(title, likes_old, likes_new, likes_new - likes_old))
                if views_new != views_old:
                    view_total += views_new - views_old
                    line = '{}：{}→{}({})'.format(title, views_old, views_new, views_new - views_old)
                    count = len([c for c in line if unicodedata.east_asian_width(c) in "FWA"])
                    if adjust_sonant_mark:
                        count -= len([c for c in line if (ord(c) == 0x3099)]) * 2
                    view_count = (views_new - views_old)
                    asta = ' '.join([('*' * 10) for i in range(view_count // 10)] + ['*' * (view_count % 10)])
                    line = '{:{width}s}{}'.format(line, asta, width=80 - count)
                    diff_views.append(line)
            else:
                like_total += likes_new
                view_total += views_new
                diff_likes.append('{}：{}'.format(title, likes_new))
                diff_views.append('{}：{}'.format(title, views_new))

    return (diff_likes, like_total, diff_views, view_total)


def line_notify(message):
    token = "nPQEoC190nfvydJRbQmY75SY00Ygvt0CxsaXWoLTUUH"
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": "Bearer " + token}
    payload = {"message": 'YouTube:\n' + message}
    requests.post(url, headers=headers, data=payload)


if __name__ == "__main__":
    json_file = '/home/pi/doc/private/python/youtube/like_count.json'
    channel_id = 'UCVD_BTWC0dmWPZOWagpEeiA'
    regular = True
    adjust_sonant_mark = False
    for arg in sys.argv[1:]:
        if arg == '-peek':
            regular = False
        if arg == '-adjust-sonant-mark':
            adjust_sonant_mark = True
    (diff_likes, like_total, diff_views, view_total) = like_count_diff(json_file, channel_id, regular, adjust_sonant_mark)
    message = None
    if len(diff_likes) > 0:
        message = "高評価：\n{}\n高評価上昇計：{}".format('\n'.join(diff_likes), like_total)

    if not regular and len(diff_views) > 0:
        if message is None:
            message = ""
        else:
            message += "\n\n"
        message += "視聴数：\n" + '\n'.join(diff_views)

    if view_total > 0:
        if message is None:
            message = ""
        else:
            message += "\n\n"
        message += "総視聴数：{}".format(view_total)

    if message is not None:
        if regular:
            line_notify(message)
        else:
            print(message)
            print(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
