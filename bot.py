# -*- coding: utf-8 -*-

import time
import eventlet
import requests
import logging
import telebot
from urllib3.poolmanager import PoolManager
from time import sleep
SINGLE_RUN = None

 # Get last 10 posts from VK group
URL_VK = 'Here is your VK-api URL'
FILENAME_VK = 'last_known_id.txt'
BASE_POST_URL = 'Base url for post'

BOT_TOKEN = 'Here is your Bot Token'
CHANNEL_NAME = 'Here is your telegram channel name'

bot = telebot.TeleBot(BOT_TOKEN)
def get_data():
    timeout = eventlet.Timeout(10)
    try:
        feed = requests.get(URL_VK)
        return feed.json()
    except eventlet.Timeout:
        logging.warning('Got Timeout while retrieving VK JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()
def send_new_posts(items, last_id):
    for item in items:
        if item['id'] <= last_id:
            break
        link = '{!s}{!s}'.format(BASE_POST_URL, item['id'])
        bot.send_message(CHANNEL_NAME, link)
        # Sleep one second. (for fix any bugs)
        time.sleep(1)
    return
def check_new_posts_vk():
    # Logging start time
    logging.info('[VK] Started scanning for new posts')
    with open(FILENAME_VK, 'rt') as file:
        last_id = int(file.read())
        if last_id is None:
            logging.error('Could not read from storage. Skipped iteration.')
            return
        logging.info('Last ID (VK) = {!s}'.format(last_id))
    try:
        feed = get_data()
        # Skip parsing, if before there was a timeout. Else parsing posts.
        if feed is not None:
            entries = feed['response'][1:]
            try:
                # Skip pinned post
                tmp = entries[0]['is_pinned']
                # Start send messages
                send_new_posts(entries[1:], last_id)
            except KeyError:
                send_new_posts(entries, last_id)
            # Save new last_id to file.
            with open(FILENAME_VK, 'wt') as file:
                try:
                    tmp = entries[0]['is_pinned']
                    # Save last_id of second post, if first post is pinned
                    file.write(str(entries[1]['id']))
                    logging.info('New last_id (VK) is {!s}'.format((entries[1]['id'])))
                except KeyError:
                    file.write(str(entries[0]['id']))
                    logging.info('New last_id (VK) is {!s}'.format((entries[0]['id'])))
    except Exception as ex:
        logging.error('Exception of type {!s} in check_new_post(): {!s}'.format(type(ex).__name__, str(ex)))
        pass
    logging.info('[VK] Finished scanning')
    return
if __name__ == '__main__':
    # Anti-spam in logs by requests library
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    # Setup logger
    logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s', level=logging.INFO,
                        filename='bot_log.log', datefmt='%d.%m.%Y %H:%M:%S')
    if not SINGLE_RUN: 
        while True:
            check_new_posts_vk()
            # 4 minutes pause
            logging.info('[App] Script went to sleep.')
            time.sleep(60 * 4)
    else:
        check_new_posts_vk()
    logging.info('[App] Script exited.\n')
