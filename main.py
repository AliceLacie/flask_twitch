from flask import Flask
import re
import requests

from datetime import datetime
from time import mktime
import hashlib
from bs4 import BeautifulSoup
import json
from dateutil import tz

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

def utc_to_kst_time(dt):
    from_zone = tz.tzutc() 
    to_zone = tz.tzlocal() 
    utc = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S') 
    utc = utc.replace(tzinfo=from_zone) 
    
    # 시간대를 변환합니다. 
    central = utc.astimezone(to_zone)
    result = str(central).split('+')[0]
    return result


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
            stream_day = str(custom_split(time_split, j)[1])
            result_day = utc_to_kst_time(stream_day)
            
            vod_list.append(custom_split(vod_split, j)[1])
            time_list.append(result_day)

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

@app.route("/")
def index():
    return 'Hello Fucking Twitch User <br> This is Fucking Twitch replay donwload API'

@app.route("/<name>")
def download(name):
    result = replay(name)
    return result

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051)