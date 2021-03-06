#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Hacks for standard library :mod:`wsgiref`.
"""

from __future__ import absolute_import

import wsgiref.simple_server
from napixd.http import Adapter


class WSGIRequestHandler(wsgiref.simple_server.WSGIRequestHandler, object):
    """
    Request Handler used to remove the escaping in the ``PATH_INFO``.
    """
    def get_environ(self):
        environ = super(WSGIRequestHandler, self).get_environ()
        if '?' in self.path:
            path, qs = self.path.split('?')
        else:
            path = self.path
        environ['PATH_INFO'] = path
        return environ


class QuietWSGIRequestHandler(WSGIRequestHandler):
    """
    Remove the log of the request in the standard output.
    """
    def log_request(self, *args, **kw):
        pass


class WSGIRefServer(Adapter):
    """
    Adapter for :mod:`napixd.http`.
    """
    def run(self, app):
        handler_cls = self.options.get('handler_class',
                                       wsgiref.simple_server.WSGIRequestHandler)
        server_cls = self.options.get('server_class',
                                      wsgiref.simple_server.WSGIServer)

        srv = wsgiref.simple_server.make_server(
            self.host, self.port, app, server_cls, handler_cls)
        srv.serve_forever()
