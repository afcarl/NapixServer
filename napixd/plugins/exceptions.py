#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WSGI middlewares to catch and export exceptions
"""

import sys
import os.path
import traceback
import json
import logging

import napixd

from napixd.exceptions import RemoteError


class ExceptionsCatcher(object):
    """
    Catch the exception raised by the decorated function.

    When an exception is caught, the traceback, the exception value
    and the details of the error are extracted and returned in a :class:`dict`.

    If *show_errors* is True, the exceptions are printed on the console.
    """
    logger = logging.getLogger('Napix.Errors')

    def __init__(self, application, show_errors=False, json=json):
        self.application = application
        self.show_errors = show_errors
        self.napix_path = os.path.dirname(napixd.__file__)
        self._json_provider = json

    def extract_error(self, environ, error):
        """
        Extract a :class:`dict` from an exception.

        It adds the keys ``request`` containing the details of the HTTP request
        causing the exception.
        """
        a, b, last_traceback = sys.exc_info()
        method = environ.get('REQUEST_METHOD')
        path = environ.get('PATH_INFO')
        self.logger.error('%s on %s failed with %s (%s)',
                          method, path, error.__class__.__name__, str(error))
        res = {
            'request': {
                'method': method,
                'path': path,
                # 'query': dict(bottle.request.GET),
            }
        }
        res.update(self.traceback_info(last_traceback))
        if isinstance(error, RemoteError):
            res.update(self.remote_exception(error))
        res.update(self.exception_details(error))
        return res

    def remote_exception(self, error):
        """
        When the error is a :exc:`napix.exceptions.HTTPError`,
        it adds the keys ``remote_call`` with the remote request description
        and ``remote_error`` with the detail of the error.
        """
        return {
            'remote_call': unicode(error.request),
            'remote_error': error.remote_error or str(error)
        }

    def traceback_info(self, last_traceback):
        """
        Extracts the informations from the traceback.

        Add the keys ``filename`` and ``line`` pointing to the root
        of the exception.
        Also adds the key ``traceback`` containing a dump of the traceback
        as a :class:`list`.
        """
        all_tb = [dict(zip(('filename', 'line', 'in', 'call'), x))
                  for x in traceback.extract_tb(last_traceback)]
        for i, frame in enumerate(all_tb):
            if not frame['filename'].startswith(self.napix_path):
                break
        else:
            i = 0

        all_tb = all_tb[i:]
        filename, lineno, function_name, text = traceback.extract_tb(
            last_traceback)[-1]

        return {
            'traceback': all_tb,
            'filename': filename,
            'line': lineno,
        }

    def exception_details(self, error):
        """
        Adds the key ``error_text`` with the string value of the exception and
        the key ``error_class`` with the class name of the exception.
        """
        return {
            'error_text': str(error),
            'error_class': error.__class__.__name__,
        }

    def __call__(self, environ, start_response):
        """
        This plugin run the view and catch the exception that are not
        :class:`HTTPResponses<bottle.HTTPResponse>`.
        The HTTPResponse are legit response and are sent to the
        :class:`napixd.plugins.conversation.ConversationPlugin`,
        the rest are errors.
        """
        try:
            return self.application(environ, start_response)
        except (MemoryError, SystemExit, KeyboardInterrupt):
            raise
        except Exception as e:
            res = self.extract_error(environ, e)
            if self.show_errors:
                traceback.print_exc()

        try:
            response = self._json_provider.dumps(res)
            content_type = 'application/json'
        except Exception as e:
            self.logger.exception('Cannot encode the error')
            response = u'Cannot encode the error: {0} while representing {1!r}'.format(e, res)
            response = response.encode('utf-8')
            content_type = 'text/plain'

        start_response('500 Internal Error', [
            ('Content-Type', content_type),
            ('Content-Length', str(len(response))),
        ])

        return [response]
