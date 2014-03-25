#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Napix proposes an option to reload the modules without stopping the server.
When the reload is triggered, the configuration is reparsed.
The autoload directories are scanned again.

When inotify is available through :mod:`pyinotify`,
it will listen to the filesystem changes to check if the auto-loaded directories changed,
and it will then issue a reload.

"""

import os
import select as original_select
import logging
import signal

try:
    from gevent import select
except ImportError:
    select = original_select


from napixd.thread_manager import run_background

__all__ = ['Reloader']

try:
    import pyinotify
except ImportError:
    pyinotify = None


logger = logging.getLogger('Napix.reload')


class Poll(object):
    """
    Le poll du pauvre (poor man's Poll)

    Transforms some usage of :class:`select.Poll`
    to :func:`select.select` calls.
    """

    def __init__(self):
        self.fd = -1

    def register(self, fd, event):
        #event is select.POLLIN
        self.fd = fd

    def unregister(self):
        self.fd = -1

    def poll(self, timeout):
        if self.fd != -1:
            read, write, empty = select.select([self.fd], [], [], timeout)
        return [(self.fd, original_select.POLLIN)]


def patch_select():
    if not hasattr(original_select, 'poll'):
        original_select.poll = Poll


class Reloader(object):
    """
    An object that checks for signals: SIGHUP,
    file changes through :mod:`pyinotify`
    or manual calls to :meth:`reload` and triggers
    a reloading of the application.
    """

    def __init__(self, app):
        self.app = app

    def start(self):
        """
        Start the daemon
        """
        signal.signal(signal.SIGHUP, self.on_sighup)

        logger.info('Launch Napix autoreloader')
        if pyinotify is not None:
            self.setup_inotify()
        else:
            logger.info(
                'Did not find pyinotify, reload on file change support disabled')

    def setup_inotify(self):
        patch_select()
        self.watch_manager = watch_manager = pyinotify.WatchManager()
        self._update_path()
        notifier = pyinotify.Notifier(watch_manager, self.on_file_change)
        run_background(notifier.loop)

    def _update_path(self):
        for path in self.app.loader.get_paths():
            if os.path.isdir(path):
                logger.info('Watch path %s', path)
                self.watch_manager.add_watch(path, pyinotify.IN_CLOSE_WRITE)

    def on_sighup(self, signum, frame):
        """
        Callback of the SIGHUP
        """
        logger.info('Caught SIGHUP, reloading')
        self.app.reload()

    def on_file_change(self, event):
        """
        Callback of the inotify call.
        """
        try:
            if (event.dir or not event.name.endswith('.py')):
                return
            logger.info('Caught file change, reloading')
            self._update_path()
            self.app.reload()
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except Exception:
            logger.exception('Ignore exception in reload loop')
