#!/usr/bin/python3
#
# Copyright (C) 2016 Braynz B.V.
# All Rights Reserved
#
# Content can not be copied and/or distributed without the express
# permission of the author.
#
# Yorick de Wid <ydw@x3.quenza.net>
#
# Version: 0.3

import sys
import os
import requests
import pyinotify
import configparser
import daemon

class Trigger(object):
        def __init__(self, cfg):
                self._cfg = cfg

        def invoke(self, msg):
                self._msg = msg
                call_method = getattr(self, 'fn_' + self._cfg['generic']['trigger'].lower())
                call_method()

        def getMessage(self):
                return 'Most recent traceback shown below\n\n' + self._msg

        def fn_ignore(self):
                pass

        def fn_mail(self):
                if (self._msg) == 0:
                        return

                request_url = 'https://api.mailgun.net/v2/{0}/messages'.format(self._cfg['mailgun']['domain'])
                request = requests.post(request_url, auth=('api', self._cfg['mailgun']['key']), data={
                        'from': 's01@mq.neuromarketingonline.nl',
                        'to': self._cfg['generic']['recipient'],
                        'subject': '[BUG REPORT :: S01.BRAYNZ.NET]',
                        'text': self.getMessage()
                })

                if request.status_code == 200:
                        print('Email sent')

class EventHandler(pyinotify.ProcessEvent):
        def my_init(self, cfg):
                self.trigger = Trigger(cfg)

        def findTrackback(self, filename):
                with open(filename) as f:
                        content = f.read()
                        ans = content.rfind('Traceback')
                        if ans > 0:
                                self.trigger.invoke(content[ans:])

        def process_IN_MODIFY(self, event):
                self.findTrackback(event.pathname)

def parseConfig(cfg):
        try:
                if 'watchlist' not in config['generic']:
                        print('set watchlist in config file')
                        sys.exit(1)
                if 'trigger' not in config['generic']:
                        print('set trigger in config file')
                        sys.exit(1)
                if 'recipient' not in config['generic']:
                        print('set recipient in config file')
                        sys.exit(1)
        except:
                sys.exit(1)

if len(sys.argv) < 2:
        print('Usage: %s [config]' % sys.argv[0])
        sys.exit(1)

# Configure watcher
config = configparser.ConfigParser()
config.read(sys.argv[1])
parseConfig(config)
print('Start watching...', config['generic']['watchlist'])

# Start watching
with daemon.DaemonContext():
        wm = pyinotify.WatchManager()
        handler = EventHandler(cfg=config)
        notifier = pyinotify.Notifier(wm, default_proc_fun=handler)
        wm.add_watch(config['generic']['watchlist'], pyinotify.IN_MODIFY)

        try:
                notifier.loop()
        except err:
                print('Starting failed')
