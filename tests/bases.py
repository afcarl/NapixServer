#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bottle
import unittest2
from cStringIO import StringIO

class WSGITester(unittest2.TestCase):
    def _make_env( self, method, url,
            body=None, localhost = True, auth=None,
            url_encoded = False,query='', agent=''):
        body_ = StringIO()
        if body:
            body_.write(body)
            body_.seek(0)
        env = {
                'wsgi.input' :body_,
                'wsgi.errors' : open('/dev/null','w'),
                'PATH_INFO': url,
                'QUERY_STRING' : query,
                'HTTP_HOST': 'napix.test',
                'REQUEST_METHOD': method,
                'SERVER_PROTOCOL' : 'HTTP/1.1',
                'HTTP_USER_AGENT' : agent,
                'HTTP_REMOTE_HOST' : localhost  and '127.0.0.1' or '1.2.3.4',
                'HTTP_AUTHORIZATION' : auth or '',
                'CONTENT_TYPE' : ( url_encoded and 'application/x-www-form-urlencoded'
                    or 'application/json'),
                'CONTENT_LENGTH' : body and len(body) or 0
                }
        if auth == False:
            env.pop('HTTP_AUTHORIZATION')
        return env

    def _start_response(self, status_line, headers):
        self.status_line = status_line
        self.headers = headers

    def _do_request(self,env):
        resp = self.bottle.wsgi(env,self._start_response)
        code,_,status = self.status_line.partition(' ')
        return int(code), dict(self.headers), ''.join(resp)

class TestServiceBase(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_request = bottle.request

    @classmethod
    def tearDownClass(cls):
        bottle.request = cls.old_request

    def _do_the_request(self,request):
        bottle.request = request
        app,args = self.bottle.match(request.environ)
        return app.call(**args)
    def _request(self,request):
        try:
            return self._do_the_request(request)
        except bottle.HTTPError,e:
            self.fail(repr(e))
    def _expect_list(self,request,lst):
        self.assertListEqual(sorted(self._request(request)),sorted(lst))
    def _expect_dict(self,request,dct):
        resp = self._request(request)
        self.assertDictEqual(resp,dct)
    def _expect_error(self,request,code):
        try:
            resp = self._do_the_request(request)
        except bottle.HTTPError,e:
            resp = e

        self.assertEqual(resp.status,code)
        return resp

    def _expect_created(self,request,url):
        try:
            resp = self._do_the_request(request)
        except bottle.HTTPResponse,e:
            resp = e
        self.assertEqual(resp.status, 201)
        self.assertEqual(resp.headers.get('Location'),url)
        return resp

    def _expect_ok(self,request):
        req = self._request(request)
        self.assertTrue(req is None)
    def _expect_405(self,request,expected_methods):
        resp = self._expect_error(request,405)
        expected_methods = set(expected_methods.split(','))
        actual_methods = set(resp.headers['Allow'].split(','))
        self.assertSetEqual(expected_methods,actual_methods)


