#!/usr/bin/env python3

import logging
import json
import os
import requests
import subprocess
import threading

from datetime import datetime, timedelta

from pip._vendor.requests.utils import stream_decode_response_unicode

from . import util

URLBASE = 'https://www.younow.com/'
BROADCASTS_PER_PAGE = 20
RTMPDUMP = './rtmpdump'
TMPDIR = './temp'

logger = logging.getLogger(__name__)
report_progress = True


class YouNow:
    def __init__(self, username):
        self.thread_count = 32
        self.username = username
        self.__user_id = None
        self.__session = None

    def download(self, broadcast_id, user_id=None, path='videos/%s'):
        logger.debug('Preparing download for %s' % str(locals()))
        broadcast_id = int(broadcast_id)

        util.ensure_directory(path % self.username)
        util.ensure_directory(TMPDIR)

        logger.debug('Getting video_path now')
        video_path = YouNow.get_videopath(broadcast_id)

        playlist_url = video_path['hls']
        logger.info('Playlist URL is %s' % playlist_url)

        playlist_path = os.path.join(TMPDIR, '%s.m3u8' % broadcast_id)
        logger.debug('Checking for Playlist at %s' % playlist_path)
        if os.path.exists(playlist_path):
            logger.info('Playlist has already been downloaded')
            with open(playlist_path, 'r') as f:
                m3u8 = f.read()
        else:
            m3u8 = YouNow.get_stream_playlist(playlist_url)
            logger.debug('Saving Playlistdata to %s' % playlist_path)
            with open(playlist_path, 'w') as f:
                f.write(m3u8)

        stream_basepath = '/'.join(playlist_url.split('/')[:-1]) + '/'
        logger.debug('stream_basepath is %s' % stream_basepath)

        broadcast_post = self.find_broadcast(broadcast_id)
        date_aired = YouNow.parse_date(broadcast_post['dateAired'])
        download = RecordDownload(m3u8, stream_basepath, '%s/%s' % (
            path % self.username, "record-%s.flv" % date_aired.strftime('%Y-%m-%d-%H-%M-%S')),
                                  thread_count=self.thread_count)
        #download.start()

        logger.debug('Removing temporary playlist')
        os.remove(playlist_path)

    def live(self, path='videos/%s'):

        util.ensure_directory(path % self.username)

        state = self.get_broadcast_state()

        broadcast_id = state['broadcastId']
        host = state['media']['host']
        app = state['media']['app']
        stream = state['media']['stream']
        date_aired = YouNow.parse_date(int(state['dateStarted']))

        streamurl = 'rtmp://%s%s/%s' % (host, app, stream)
        i = 1
        while True:
            filename = path % '%s/%s_live_%s_%s_%d.flv' % (
                self.username,
                self.username,
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

    @staticmethod
    def get_stream_playlist(url):
        r = requests.get(url)
        return r.text

    def download_from_playlist(self, basepath, m3u8, path, chunksize=1048576):
        logger.info('Starting download by playlistfile to %s' % path)
        files = []
        for line in m3u8.split('\n'):
            filename = line.strip()
            if filename and filename[0] != '#':
                files.append(filename)

        logger.info('Stream has been splitted in %d parts' % len(files))
        files_downloaded = 1
        current_filesize = 0
        with open(path, 'wb') as f:
            for filename in files:
                url = basepath + filename
                logger.debug('Requesting %s' % url)
                r = requests.get(url, stream=True)
                for chunk in r.iter_content(chunk_size=chunksize):
                    if chunk:
                        bytes_written = f.write(chunk)
                        current_filesize += bytes_written
                if report_progress:
                    logger.info('%8.d/%8.d\t%s' % (files_downloaded, len(files), util.human_format(current_filesize)))
                files_downloaded += 1

    @staticmethod
    def parse_date(datestr):
        if type(datestr) is int:
            val = datetime.fromtimestamp(datestr)
            return val
        else:
            val = datetime.strptime(datestr, '%Y-%m-%d %H:%M:%S')
        return val + timedelta(hours=6)

    def find_broadcast(self, broadcast_id):
        start_from = 0
        while True:
            allbroadcasts = self.get_broadcasts(start_from)
            if allbroadcasts is None:
                return None

            for broadcast in allbroadcasts:
                if broadcast['media']['broadcast']['broadcastId'] == broadcast_id:
                    return broadcast['media']['broadcast']
            start_from += BROADCASTS_PER_PAGE
        return None

    def get_broadcastinfo(self, broadcast_id):
        logger.debug('Getting Broadcastinfo')
        r = requests.get(URLBASE + '/php/api/post/get/entityId=%s/deepLink=b/channelId=%s' % (broadcast_id, self.user_id))
        return r.json()

    def get_broadcasts(self, start_from=0):
        logger.debug('Getting Broadcasts starting at %s' % start_from)
        r = requests.get(URLBASE + 'php/api/post/getBroadcasts/channelId=%s/startFrom=%s' % (self.user_id, start_from))
        return r.json()['posts']

    @staticmethod
    def _get_session():
        logger.debug('Getting a session')
        r = requests.get(URLBASE + 'php/api/younow/user')
        return r.json()

    def get_broadcast_state(self):
        logger.debug('Getting broadcast state/user state')
        r = requests.get(URLBASE + 'php/api/broadcast/info/user=%s' % self.
                         username)
        try:
            return r.json()
        except json.decoder.JSONDecodeError as e:
            print(r)
            raise e

    def _get_userid(self):
        return self.get_broadcast_state()['userId']

    @staticmethod
    def get_videopath(broadcast_id):
        logger.debug('Getting videopath')
        r = requests.get('http://www.younow.com/php/api/broadcast/videoPath/broadcastId=%s' % broadcast_id)
        return r.json()

    def is_live(self):
        return 'media' in self.get_broadcast_state()

    def get_user_id(self):
        if not self.__user_id:
            self.__user_id = self._get_userid()
        return self.__user_id

    def get_session(self):
        if not self.__session:
            self.__session = YouNow._get_session()
        return self.__session

    user_id = property(get_user_id)
    session = property(get_session)


class RecordDownload(object):
    def __init__(self, m3u8, stream_basepath, filepath, thread_count=1):
        self._m3u8 = m3u8
        self._filepath = filepath
        self._stream_basepath = stream_basepath
        self._thread_count = thread_count
        self.__download_buffer = [None] * thread_count
        self.__threads = [None] * thread_count
        self.download_chunksize = 1 << 20
        self.current_filesize = 0
        self.files_downloaded = 0
        self._filehandle = None
        self._files = []

    def download_chunk(self, url, slot):
        self.__download_buffer[slot] = b''
        logger.debug('Requesting %s' % url)
        r = requests.get(url, stream=True)
        for chunk in r.iter_content(chunk_size=self.download_chunksize):
            if chunk:
                self.__download_buffer[slot] += chunk

    def _create_thread(self, filename, slot):
        url = self._stream_basepath + filename
        thread = threading.Thread(target=self.download_chunk, args=(url, slot))
        return thread

    def _process_thread(self, slot):
        if self.__threads[slot]:
            self.__threads[slot].join()
            self.current_filesize += self._filehandle.write(self.__download_buffer[slot])
            self.files_downloaded += 1
            if report_progress:
                logger.info('%8.d/%.8d\t%s' % (
                    self.files_downloaded, len(self._files), util.human_format(self.current_filesize)))

    def _generate_filelist(self, m3u8):
        for line in m3u8.split('\n'):
            filename = line.strip()
            if filename and filename[0] != '#':
                self._files.append(filename)

    def start(self):
        logger.info('Starting download by playlistfile to %s' % self._filepath)
        self._generate_filelist(self._m3u8)

        logger.info('Stream has been splitted in %d parts' % len(self._files))
        file_iter = iter(self._files)

        for slot in range(self._thread_count):
            try:
                filename = next(file_iter)
                self.__threads[slot] = self._create_thread(filename, slot)
                self.__threads[slot].start()
            except StopIteration:
                break

        with open(self._filepath, 'wb') as self._filehandle:
            while True:
                slot = slot + 1 if (slot + 1) < self._thread_count else 0
                self._process_thread(slot)
                try:
                    filename = next(file_iter)
                    self.__threads[slot] = self._create_thread(filename, slot)
                    self.__threads[slot].start()
                except StopIteration:
                    logger.debug('No more files. Finishing downloads')
                    break

            # wait for the last threads to finish
            for slot in range(self._thread_count):
                self._process_thread(slot)
        logger.debug('Last thread finished')
