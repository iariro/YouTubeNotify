#!/usr/bin/python3

# -*- coding: utf-8 -*-

from os import getenv
import json
import googleapiclient.discovery

api_service_name = "youtube"
api_version = "v3"


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_authenticated_service(developerKey):
    return googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=developerKey)


def get_uploads_playlist_id(youtube, channelId):
    request = youtube.channels().list(
        part="contentDetails",
        id=channelId,
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
        video_id_list.extend(list(map(lambda item: item["snippet"]["resourceId"]["videoId"], response["items"])))
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
            fields="items(id,snippet(title,description,publishedAt,thumbnails),statistics(viewCount,likeCount))"
        )
        response = request.execute()
        video_items.extend(response["items"])

    return video_items


def get_image_url(video_item):
    qualities = ['standard', 'high', 'medium', 'default']
    for quality in qualities:
        if quality in video_item['snippet']['thumbnails'].keys():
            return video_item['snippet']['thumbnails'][quality]['url']
    return ''


def convertVideoItems(video_items):
    return { item["id"]: {
            'title': item["snippet"]["title"],
            'views': int(item["statistics"]["viewCount"]),
            'likes': int(item["statistics"]["likeCount"]) } for item in video_items}


def like_count_diff(json_file, channelId):
    with open(json_file, 'r') as f:
        video_items_json_old = json.load(f)

    youtube = get_authenticated_service('AIzaSyBuV44B4RZq90SnDs_GvCz7zXwrR34ixXI')
    uploads_playlist_id = get_uploads_playlist_id(youtube, channelId)
    video_id_list = get_video_id_in_playlist(youtube, uploads_playlist_id)
    video_items = get_video_items(youtube, video_id_list)
    video_items_json = convertVideoItems(video_items)
    with open(json_file, 'w') as f:
        json.dump(video_items_json, f, indent=4, ensure_ascii=False)

    diff = []
    for video_id in video_items_json:
        if video_id in video_items_json_old:
            if video_items_json[video_id]['likes'] != video_items_json_old[video_id]['likes']:
                diff.append('%sの高評価：%d→%d'.format(video_items_json[video_id]['title'],
                                                        video_items_json_old[video_id]['likes'],
                                                        video_items_json[video_id]['likes']))
        else:
            diff.append('%sの高評価：%d'.format(video_items_json[video_id]['title'],
                                                video_items_json[video_id]['likes']))
    return diff

def line_notify(message):
    token = "nPQEoC190nfvydJRbQmY75SY00Ygvt0CxsaXWoLTUUH"
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": "Bearer " + token}
    payload = {"message": 'YouTube:\n' + message}
    requests.post(url, headers=headers, data=payload)

if __name__ == "__main__":
    json_file = '/home/pi/doc/private/python/youtube/my_videos.json'
    diff = like_count_diff(json_file, 'UCVD_BTWC0dmWPZOWagpEeiA')
    line_notify('\n'.join(diff)):
