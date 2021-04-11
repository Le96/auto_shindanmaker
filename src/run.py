#!/usr/bin/env python

import datetime
import requests
import time
import urllib

import bs4
import schedule
import tweepy

from env.credentials import *

USERNAME = 'れくろ'
TARGET_ID = {
    'daily': (503025, 763660)
}


def build_api() -> tweepy.API:
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN_KEY, ACCESS_TOKEN_SECRET)
    return tweepy.API(auth, wait_on_rate_limit=True,
                      wait_on_rate_limit_notify=True)


def print_now():
    print(datetime.datetime.now())


def shindan(shindan_id: int, username: str, api: tweepy.API = None,
            dry_run: bool = False) -> None:
    payload = {'u': username}
    resp = requests.post('https://shindanmaker.com/' + str(shindan_id),
                         data=payload)
    if not resp.ok:
        print('error has occured')
        return
    soup = bs4.BeautifulSoup(resp.text, 'html.parser')
    shindan_url = soup.select('span.btn-twitter.btn-share-lg')[0]\
                      .attrs['daat-share_url']
    shindan_result = list(urllib.parse.parse_qs(shindan_url).values())[0][0]
    if not api:
        api = build_api()
    if not dry_run:
        api.update_status(shindan_result)
    print(shindan_id)
    print(shindan_result)


def main():
    # prebuild twitter api
    api = build_api()
    # print time
    schedule.every().day.at('00:00').do(print_now)
    # daily shindan
    for target_id in TARGET_ID['daily']:
        schedule.every().day.at('00:00').do(shindan, shindan_id=target_id,
                                            username=USERNAME, api=api)
    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == '__main__':
    main()
