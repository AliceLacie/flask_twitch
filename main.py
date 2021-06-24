from flask import Flask, request
import re
import requests

from datetime import datetime
from time import mktime
import hashlib
import re
from bs4 import BeautifulSoup
import json

app = Flask(__name__)

s = requests.session()

header = {'User-Agent': 'Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)'}
vod_split = 'streams/', '">'
time_split='<span>', '</span>'
day_time = ' ', ':'

def change_utc(dt): 
    time_format = '%Y-%m-%d %H:%M:%S'
    time_str = dt
    now = datetime.strptime(time_str, time_format)
    time_tuple = now.timetuple()
    utc_now = mktime(time_tuple)
    return int(utc_now)

def custom_split(sepr_list, str_to_split):
    regular_exp = '|'.join(map(re.escape, sepr_list))
    return re.split(regular_exp, str_to_split)

def replay(streamername):
    m3u8_list = []
    flag = ''
    cnt = 0

    print('\n[ + ] Parsing video numbers and time...\n')

    vodID_html = s.get(f'https://twitchtracker.com/{streamername}/streams', headers=header).text
    soup = BeautifulSoup(vodID_html, 'lxml')
    pasing = soup.find_all('a')

    vod_list= []
    time_list = []

    for i in pasing:
        j = str(i)
        if f'<a href="/{streamername}/streams/' in j:
            stream_day = str(custom_split(time_split, j)[1]).split()
            retime = int(stream_day[1].split(':')[0])
            stime = stream_day[1].split(':')[0]

            if retime+9 >= 24: retime = retime+9-24
            else: retime+=9

            if retime < 10:
                retime= f'0{retime}' 

            stream_day[1] = stream_day[1].replace(stime, str(retime), 1)
            fin_time = f'{stream_day[0]} {stream_day[1]}'

            vod_list.append(custom_split(vod_split, j)[1])
            time_list.append(fin_time)

    for i,j in zip(vod_list, time_list):
        stream_vodID_time = f'{streamername}_{i}_{str(change_utc(j))}'
        hash = str(hashlib.sha1(stream_vodID_time.encode('utf-8')).hexdigest())
        hash = hash[:20]
        hash_stream_vodID_time = f'{hash}_{stream_vodID_time}'
        url = f"https://d1m7jfoe9zdc1j.cloudfront.net/{hash_stream_vodID_time}/chunked/index-dvr.m3u8"
        m3u8_list.append(url)
    result = {}

    for i, j in zip(time_list[::-1], m3u8_list[::-1]):
        result[cnt] = [i,j]
        cnt+=1

    json_result = json.dumps(result)

    return json_result


@app.route("/<name>")
def index(name):
    result = replay(name)
    return result

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5051)