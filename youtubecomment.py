import datetime
import requests
import json
import sys

URL = 'https://www.googleapis.com/youtube/v3/'
API_KEY = 'AIzaSyBuV44B4RZq90SnDs_GvCz7zXwrR34ixXI'
authorChannelId = 'UCVD_BTWC0dmWPZOWagpEeiA'

def line_notify(message):
    token = "nPQEoC190nfvydJRbQmY75SY00Ygvt0CxsaXWoLTUUH"
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": "Bearer " + token}
    payload = {"message": 'YouTube:' + message}
    requests.post(url, headers=headers, data=payload)

def print_video_comment(video, n=10):
    params = {
        'key': API_KEY,
        'part': 'snippet',
        'videoId': video['video_id'],
        'order': 'relevance',
        'textFormat': 'plaintext',
        'maxResults': n,
        'searchTerms': 'k k',
    }
    response = requests.get(URL + 'commentThreads', params=params)
    resource = response.json()

    if 'items' not in resource:
        return

    cnt = 0
    datetime_author = {}
    for comment_info in resource['items']:
        snippet = comment_info['snippet']['topLevelComment']['snippet']
        # 名前
        authorDisplayName = snippet['authorDisplayName']
        # コメント
        text = snippet['textDisplay']
        # グッド数
        likeCount = snippet['likeCount']
        # 返信数
        totalReplyCount = comment_info['snippet']['totalReplyCount']
        # コメント日時
        publishedAt = snippet['publishedAt']
        datetime_author[publishedAt] = snippet['authorChannelId']['value']

        if snippet['authorChannelId']['value'] != authorChannelId:
            continue

        if (publishedAt not in video):
            f = '{}\n{}\n{}\nグッド数: {} 返信数: {}\n{}\n'
            print(f.format(video['title'],
                           authorDisplayName,
                           text,
                           likeCount,
                           totalReplyCount,
                           publishedAt))
        elif (video[publishedAt]['likeCount'] != likeCount or video[publishedAt]['totalReplyCount'] != totalReplyCount):
            f = '{}\n{}\n{}\nグッド数: {}→{} 返信数: {}→{}\n{}\n'
            message = f.format(video['title'],
                               authorDisplayName,
                               text,
                               video[publishedAt]['likeCount'],
                               likeCount,
                               video[publishedAt]['totalReplyCount'],
                               totalReplyCount,
                               publishedAt)
            print(message)
            line_notify(message)

        if publishedAt not in video:
            video[publishedAt] = {}
        video[publishedAt]['totalReplyCount'] = totalReplyCount
        video[publishedAt]['likeCount'] = likeCount
        cnt += 1

#   delkeys = []
#   for key in video:
#       if key == 'title' or key == 'video_id':
#           continue
#       if datetime_author[key] != authorChannelId:
#           delkeys.append(key)
#           print('del', video['video_id'], key, datetime_author[key])
#   for key in delkeys:
#       del video[key]

    return cnt

if len(sys.argv) < 2:
    print('Usage: jsonfile')
    exit()

print(datetime.datetime.now())
for jsonfile in sys.argv[1:]:
    # read json
    with open(jsonfile, 'r') as file:
        data = json.load(file)

    print(jsonfile)
    cnt = 0
    for site in data['sites']:
        if site['video_id'] != '':
            try:
                cnt2 = print_video_comment(site, n=100)
                if cnt2:
                    if cnt2 == 0:
                        print('_', end='', flush=True)
                    else:
                        print('o', end='', flush=True)
                    cnt += cnt2
                else:
                    print('x', end='', flush=True)
            except Exception as exception:
                print('e', end='', flush=True)

    print('(%d)' % cnt)

    with open(jsonfile, 'w') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
