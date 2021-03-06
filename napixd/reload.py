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
import threading
import signal
import functools

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

    Transforms some usage of :class:`select.Poll` to :func:`select.select` calls.
    """

    def __init__(self):
        self.fd = -1

    def register(self, fd, event):
        # event is select.POLLIN
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


# https://gist.github.com/walkermatt/2871026
def debounce(wait):
    """ Decorator that will postpone a functions execution until after *wait*
    seconds have elapsed since the last time it was invoked. """

    def decorator(fn):
        @functools.wraps(fn)
        def debounced(self):
            try:
                debounced.t.cancel()
            except(AttributeError):
                pass
            debounced.t = threading.Timer(wait, fn, (self, ))
            debounced.t.start()
        return debounced
    return decorator


class Reloader(object):
    """
    An object that checks for signals: SIGHUP, file changes through
    :mod:`pyinotify` and triggers a reloading of the application by calling
    :meth:`napixd.application.Napixd.reload`.
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
        """
        Set up the watch in the directories given by
        :meth:`~napixd.loader.loader.Loader.get_paths` for file system events by
        :mod:`pyinotify`.
        """
        patch_select()
        self.watch_manager = watch_manager = pyinotify.WatchManager()
        self._update_path()
        notifier = pyinotify.Notifier(watch_manager, self.on_file_change)
        run_background(notifier.loop)

    @debounce(1)
    def reload(self):
        logger.info('Reloading')
        self._update_path()
        self.app.reload()

    def _update_path(self):
        for path in self.app.loader.get_paths():
            if os.path.isdir(path):
                logger.info('Watch path %s', path)
                self.watch_manager.add_watch(path, pyinotify.IN_CLOSE_WRITE,
                                             rec=True, auto_add=True)

    def on_sighup(self, signum, frame):
        """
        Callback of the SIGHUP
        """
        logger.info('Caught SIGHUP, reloading')
        self.reload()

    def on_file_change(self, event):
        """
        Callback of the inotify call.
        """
        try:
            if (event.dir or not event.name.endswith('.py')):
                return
            logger.debug('Caught file change, reloading')
            self.reload()
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except Exception:
            logger.exception('Ignore exception in reload loop')
