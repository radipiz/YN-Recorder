#!/usr/bin/env python3
import json
import os
import requests
import subprocess

from datetime import datetime, timedelta
from pprint import pprint

from . import util

URLBASE = 'https://www.younow.com/'
BROADCASTS_PER_PAGE = 20
RTMPDUMP = './rtmpdump'

class YouNow:

    def __init__(self):
        self.session = self.get_session()

    def download(self, username, broadcast_id, user_id = None, path='videos/%s'):
        broadcast_id = int(broadcast_id)

        util.ensure_directory(path % username)

        # get User ID if not passed
        user_id = user_id if user_id is not None else self.get_broadcast_state(username)['userId']
        b_info = self.get_broadcastinfo(user_id, broadcast_id)
        video_path = self.get_videopath(broadcast_id)
        sessionid = self.session['session']

        mybroadcast = self.find_broadcast(user_id, broadcast_id)

        if mybroadcast is None:
            raise RuntimeError('Cannot find broadcast in broadcast list')
        date_aired = self.parse_date(mybroadcast['dateAired'])
        filename = "record-%s.flv" % date_aired.strftime('%Y-%m-%d-%H-%M-%S')
        print('Downloading broadcast from %s' % str(date_aired))
        args = [RTMPDUMP, '-v', 
                '-o', '%s/%s' % (path % username, filename), 
                '-r', '%s%s?sessionId=%s' % (video_path['server'], video_path['stream'], sessionid),
                '-p', URLBASE]
        dl_proc = subprocess.Popen(args, stdout=subprocess.PIPE)
        lines_iterator = iter(dl_proc.stdout.readline, b"")
        for line in lines_iterator:
            print(line)

    def live(self, username, path='videos/%s'):
        
        util.ensure_directory(path % username)
        
        state = self.get_broadcast_state(username) 

        broadcast_id = state['broadcastId']
        host = state['media']['host']
        app = state['media']['app']
        stream = state['media']['stream']
        date_aired = self.parse_date(int(state['dateStarted']))
        
        streamurl = 'rtmp://%s%s/%s' % (host, app, stream)
        i = 1
        while True:
            filename = path % '%s/%s_live_%s_%s_%d.flv' % (
                    username, 
                    username, 
                    date_aired.strftime('%Y-%m-%d-%H-%M-%S'),
                    broadcast_id, i)
            if not os.path.exists(filename):
                break
            i += 1
        print('Start downloading now (%s)' % filename)
        args = [RTMPDUMP, '-v', 
                '-o', filename, 
                '-r', streamurl]
        dl_proc = subprocess.Popen(args, stdout=subprocess.PIPE)
        lines_iterator = iter(dl_proc.stdout.readline, b"")
        for line in lines_iterator:
            print(line)


    def parse_date(self, datestr):
        if type(datestr) is int:
            val = datetime.fromtimestamp(datestr)
            return val
        else:
            val = datetime.strptime(datestr, '%Y-%m-%d %H:%M:%S')
        return val + timedelta(hours=6)

    def find_broadcast(self, user_id, broadcast_id):
        start_from = 0
        while True:
            allbroadcasts = self.get_broadcasts(user_id, start_from)
            if allbroadcasts is None:
                return None

            for broadcast in allbroadcasts:
                if broadcast['media']['broadcast']['broadcastId'] == broadcast_id:
                    return broadcast['media']['broadcast']
            start_from += BROADCASTS_PER_PAGE
        return None

    def get_broadcastinfo(self, user_id, broadcast_id):
        print('Getting Broadcastinfo')
        r = requests.get(URLBASE + '/php/api/post/get/entityId=%s/deepLink=b/channelId=%s' % (broadcast_id, user_id))
        return r.json()

    def get_broadcasts(self, user_id, start_from=0):
        print('Getting Broadcasts starting at %s' % start_from)
        r = requests.get(URLBASE + 'php/api/post/getBroadcasts/channelId=%s/startFrom=%s' % (user_id, start_from))
        return r.json()['posts']

    def get_session(self):
        print('Getting a session')
        r = requests.get(URLBASE + 'php/api/younow/user')
        return r.json()
   
    def get_broadcast_state(self, username):
        print('Getting broadcast state/user state')
        r = requests.get(URLBASE + 'php/api/broadcast/info/user=%s' % username)
        try:
            return r.json()
        except json.decoder.JSONDecodeError as e:
            print(r)
            raise e

    def get_userid(self, username):
        return self.get_broadcast_state(username)['userId']

    def get_videopath(self, broadcast_id):
        print('Getting videopath')
        r = requests.get('http://www.younow.com/php/api/broadcast/videoPath/broadcastId=%s' % broadcast_id)
        return r.json()
    
    def is_live(self, username):
        return 'media' in self.get_broadcast_state(username)

