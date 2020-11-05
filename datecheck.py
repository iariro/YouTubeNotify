import json
import sys

if len(sys.argv) < 2:
    print('Usage: jsonfile')
    exit()

for jsonfile in sys.argv[1:]:
    # read json
    with open(jsonfile, 'r') as file:
        data = json.load(file)

    print(jsonfile)
    for site in data['sites']:
        dates = []
        for key, value in site.items():
            if key == 'title':
                title = value
            elif key == 'video_id':
                pass
            else:
                dates.append(key)

        for d in dates:
            if len(d) == 20:
                d2 = d.replace('Z', '.000Z')
                if d2 not in dates:
                    print(title)
                    print('\t' + d2 + ' not pair')
            elif len(d) == 24:
                d2 = d.replace('.000Z', 'Z')
                if d2 not in dates:
                    print(title)
                    print('\t' + d2 + ' not pair')
