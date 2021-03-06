#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A WSGI server implementation
"""

import time
import logging
import json

from napixd.http.router.router import Router
from napixd.http.request import Request, HeadersDict
from napixd.http.response import HTTPError, Response, HTTPResponse, HTTP404

logger = logging.getLogger('Napix.conversations')

__all__ = ('WSGIServer', )

block_size = 1024**2


def file_wrapper(environ, filelike):
    if 'wsgi.file_wrapper' in environ:
        return environ['wsgi.file_wrapper'](filelike, block_size)
    else:
        return iter(lambda: filelike.read(block_size), '')


class WSGIServer(object):
    """
    A WSGI compliant server used for napixd.
    """
    def __init__(self, json=json):
        self._router = r = Router()
        self._routers = [r]
        self._json_provider = json

    def __call__(self, environ, start_response):
        environ['napixd.request'] = request = Request(environ, self._json_provider)
        try:
            resp = self.handle(request)
        except HTTPError as error:
            resp = error

        resp = self.cast(request, resp)
        headers = resp.headers
        headers['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
        headers['Server'] = 'napixd'

        start_response(resp.status_line, headers.items())
        return resp.body

    def __repr__(self):
        rep = []
        for router in self._routers:
            rep.append(repr(router))
        return '\n----\n'.join(rep)

    def handle(self, request):
        """
        Handles the request: :meth:`resolve` it and executes it
        or raises a :class:`napixd.http.response.HTTP404`.
        """
        callback = self.resolve(request.path)
        if callback is None:
            return HTTP404()
        return callback(request)

    def resolve(self, target):
        """
        Resolves the route at target.

        The first router having a match is used. If there is no match,
        ``None`` is returned.
        """
        for router in reversed(self._routers):
            resolved = router.resolve(target)
            if resolved is not None:
                return resolved

    @property
    def router(self):
        """
        The first router of the server
        """
        return self._router

    def route(self, url, callback, **kw):
        """
        Add a route using the first :attr:`router`.
        """
        return self._router.route(url, callback, **kw)

    def unroute(self, url, all=False):
        """
        Remove a route from the :attr:`router`.
        """
        return self._router.unroute(url, all=all)

    def push(self, router=None):
        """
        Adds and returns a router at the end of the stack.

        If *router* is ``None``, a new :class:`~napixd.http.router.router.Router` is created.
        """
        if router is None:
            router = Router()
        self._routers.append(router)
        return router

    def pop(self, router):
        """
        Removes the *router* from the stack.
        """
        if router is self._router:
            raise ValueError('Cannot pop internal router')
        self._routers.remove(router)

    def cast(self, request, response):
        """
        Translates a response in a :class:`napixd.http.response.HTTPResponse`
        object.
        """
        if isinstance(response, Response):
            return HTTPResponse(200, response.headers, response)
        elif isinstance(response, (HTTPError, HTTPResponse)):
            status = response.status
            body = response.body
            headers = response.headers
        else:
            status = 200
            headers = HeadersDict()
            body = response

        if request.method == 'HEAD':
            body = None
            headers['Content-Length'] = 0

        content_type = headers.get('Content-Type', '')
        content_length = headers.get('Content-Length', None)

        if isinstance(body, basestring):
            if not content_type:
                content_type = 'text/plain'
            if isinstance(body, unicode):
                content_type += '; charset=utf-8'
                body = body.encode('utf-8')
        elif hasattr(body, 'read'):
            body = file_wrapper(request.environ, body)
        elif body is not None:
            content_type = 'application/json'
            body = self._json_provider.dumps(body)
        else:
            content_type = ''
            body = []

        if isinstance(body, str):
            content_length = len(body)
            body = [body]

        headers.setdefault('Content-Type', content_type)
        if content_length is not None:
            headers.setdefault('Content-Length', content_length)
        return HTTPResponse(status, headers, body)
