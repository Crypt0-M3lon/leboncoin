#!/usr/bin/python
# -*- coding: UTF-8 -*-


class Stdout:
    def alert(self, alerts):
        for alert in alerts:
            print alert


def init(config):
    return Stdout()