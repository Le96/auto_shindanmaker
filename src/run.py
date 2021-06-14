#!/usr/bin/env python

import argparse
import datetime
import time
import urllib

import requests

import bs4
import schedule
import tweepy

from env.credentials import ACCESS_TOKEN_KEY, ACCESS_TOKEN_SECRET, \
                            CONSUMER_KEY, CONSUMER_SECRET

USERNAME = 'れくろ'
TARGET_ID = {
    'daily': {0: (503025, 763660)},
    'monthly': {5: (785372, )},
    'annual': {(3, 1): (618137, )}
}


def build_api() -> tweepy.API:
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN_KEY, ACCESS_TOKEN_SECRET)
    return tweepy.API(auth, wait_on_rate_limit=True,
                      wait_on_rate_limit_notify=True)


def print_now():
    print(datetime.datetime.now())


def shindan(shindan_id: int, username: str, api: tweepy.API = None,
            dry_run: bool = False, month: int = None, day: int = None) -> None:
    if month and datetime.date.today().month != month:
        print(shindan_id,
              'skipped: today is not specified month({}).'.format(month))
        return
    if day and datetime.date.today().day != day:
        print(shindan_id,
              'skipped: today is not specified day({}).'.format(day))
        return
    session = requests.session()
    resp = session.get('https://shindanmaker.com/' + str(shindan_id))
    soup = bs4.BeautifulSoup(resp.text, 'html.parser')
    token = soup.select_one('[name="_token"]')['value']
    hidname = soup.select_one('[name="hiddenName"]')['value']
    data = {'_token': token, 'name': username, 'hiddenName': hidname}
    resp = session.post('https://shindanmaker.com/' + str(shindan_id),
                        data=data, cookies=resp.cookies)
    soup = bs4.BeautifulSoup(resp.text, 'html.parser')
    shindan_result = soup.select_one('#copy-textarea-140').text
    if not api:
        api = build_api()
    if not dry_run:
        api.update_status(shindan_result)
    print(shindan_id)
    print(shindan_result)


def main(first_dry_run: bool = False):
    # prebuild twitter api
    api = build_api()
    # print time
    schedule.every().day.at('00:00').do(print_now)
    # daily shindan
    for hour, target_ids in TARGET_ID['daily'].items():
        for target_id in target_ids:
            # first time execute
            shindan(shindan_id=target_id, username=USERNAME, api=api,
                    dry_run=first_dry_run)
            schedule.every().day.at('{:02d}:00'.format(hour)).do(
                shindan, shindan_id=target_id, username=USERNAME, api=api)
    for day, target_ids in TARGET_ID['monthly'].items():
        for target_id in target_ids:
            shindan(shindan_id=target_id, username=USERNAME, api=api,
                    dry_run=first_dry_run)
            schedule.every().day.at('00:00').do(shindan, shindan_id=target_id,
                                                username=USERNAME, api=api,
                                                day=day)
    for date, target_ids in TARGET_ID['annual'].items():
        for target_id in target_ids:
            shindan(shindan_id=target_id, username=USERNAME, api=api,
                    dry_run=first_dry_run)
            schedule.every().day.at('00:00').do(shindan, shindan_id=target_id,
                                                username=USERNAME, api=api,
                                                month=date[0], day=date[1])
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Automatic shindan tool.')
    parser.add_argument('--dry-run', action='store_true',
                        help='suppress tweet of first time run.')
    args = parser.parse_args()
    main(first_dry_run=args.dry_run)
