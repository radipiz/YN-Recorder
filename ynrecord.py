#!/usr/bin/env python3

import argparse
import logging
import os
from lib import yn


def main():
    args = parse_args()
    if yn.URLBASE in args.start:
        # record more
        proceed_url(args.start)
    else:
        proceed_user(args.start, live_yes=args.yes, only_live=args.onlylive)


def proceed_user(username, live_yes=False, only_live=False):
    client = yn.YouNow(username)
    answer = 'n'
    if client.is_live():
        if not live_yes:
            answer = input('[LIVE] %s is streaming right now! Start downloading? (y/n): ' % username)
        if answer.lower() == 'y' or live_yes:
            if already_downloading(username):
                logger.error('Alreading downloading livestream. Aborting')
                return
            print('Recording Livestream now')
            live(client, username)
            return
    if only_live:
        print('%s is not live :(' % username)
        return False
    start_from = 0
    try:
        while answer.lower() == 'n':
            broadcasts = client.get_broadcasts(start_from)
            if broadcasts is None:
                print('No more Broadcasts')
                return
            print('Showing %d broadcasts starting at %d' % (yn.BROADCASTS_PER_PAGE, start_from))
            for b in broadcasts:
                bdata = b['media']['broadcast']
                print('\t[%d] %s (%s)' % (
                    bdata['broadcastId'],
                    client.parse_date(bdata['dateAired']),
                    bdata['broadcastLengthMin']))
            answer = input('Streamid, \'n\' for next or blank to exit: ')
            try:
                broadcast_id = int(answer)
                client.download(broadcast_id)
            except ValueError as e:
                logging.error('Something went wrong: ', e)
                pass
            if answer.lower() == 'n':
                start_from += yn.BROADCASTS_PER_PAGE
    except PermissionError:
        logging.error('Permission Denied! Either YN changed the API or the use somehow hides their broadcasts')



def live(client, username):
    lockfile = 'live-%s.lock' % username
    open(lockfile, 'w').close()
    try:
        client.live()
    except Exception as e:
        print(e)
        pass
    finally:
        os.unlink(lockfile)


def already_downloading(username):
    lockfile = 'live-%s.lock' % username
    return os.path.exists(lockfile)


def proceed_url(url):
    # https://www.younow.com/Drache_Offiziell/73754130/0/FeDInMTj/b/November-1,-2015
    parts = url.split('/')
    username = parts[3]
    broadcast_id = parts[4]
    salad = parts[6]
    client = yn.YouNow(username)
    logger.info('Trying to download the stream %s from %s' % (broadcast_id, username))
    client.download(broadcast_id)


def parse_args():
    parser = argparse.ArgumentParser(description='Records Streams from YouNow')
    parser.add_argument('start', action='store', help='An username or record url')
    parser.add_argument('--yes', action='store_const', const=True, required=False,
                        help='Anwers yes to any y/n questions')
    parser.add_argument('--onlylive', action='store_const', const=True, required=False,
                        help='Checks only if the user is live and quits otherwise')
    return parser.parse_args()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    main()

