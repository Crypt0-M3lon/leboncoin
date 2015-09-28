#!/usr/bin/python
# -*- coding: UTF-8 -*-

import tweepy


class Twitter:
    auth = None
    api = None

    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(self.auth)

    def alert(self, alerts):
        for alert in alerts:
            if len(alert) > 140:
                alert=alert[:140]
            try:
                self.api.update_status(status=alert)
            except tweepy.error.TweepError as e:
                pass


def init(config):
    return Twitter(config['consumer_key'],config['consumer_secret'],config['access_token'],config['access_token_secret'])
