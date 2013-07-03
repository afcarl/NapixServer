#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import types
import unittest2
import mock
import bottle
from tests.mock.managers import get_managers

from napixd.managers.actions import action
from napixd.exceptions import ValidationError, NotFound
from napixd.conf import Conf
from napixd.services import BaseCollectionService, FirstCollectionService
from napixd.services.servicerequest import ServiceActionRequest, ServiceResourceRequest, ServiceCollectionRequest

class _Test( unittest2.TestCase):
    def _make( self, method, **kw ):
        self.Manager, self.Managed, x = get_managers()
        self.managed = self.Managed.return_value
        self.manager = self.Manager.return_value

        self.patch_request = mock.patch( 'bottle.request', method=method, **kw)
        self.request = self.patch_request.start()
        self.addCleanup( self.patch_request.stop)

        self.fcs_conf = mock.Mock( spec=Conf, name='fcs_conf')
        self.cs_conf = mock.Mock( spec=Conf, name='cs_conf')

        self.fcs = FirstCollectionService( self.Manager, self.fcs_conf, 'parent')
        self.cs = BaseCollectionService( self.fcs, self.Managed, self.cs_conf, 'child')

class _TestSCR( _Test):
    def _make( self, method, **kw):
        if not 'GET' in kw:
            kw['GET'] = {}
        super( _TestSCR, self)._make( method, **kw)
        self.scr = ServiceCollectionRequest([ 'p1'], self.cs)

class TestCollectionServiceRequest( _TestSCR):
    def setUp(self):
        self._make( 'GET')

    def test_get(self):
        self.managed.list_resource.return_value = [ 1, 2, 3]
        self.manager.validate_id.side_effect = lambda y:y
        s = self.scr.handle()
        self.assertListEqual( s, ['/parent/p1/child/1',
            '/parent/p1/child/2',
            '/parent/p1/child/3'])
        self.manager.get_resource.assert_called_once_with( 'p1')
        self.managed.list_resource.assert_called_once_with()

    def test_get_invalid_id(self):
        self.manager.validate_id.side_effect = ValidationError()
        with self.assertRaises( bottle.HTTPError) as resp:
            self.scr.handle()
        self.assertEqual( resp.exception.status_code, 400)

    def test_get_not_found(self):
        self.manager.validate_id.side_effect = NotFound('not found')
        with self.assertRaises( bottle.HTTPError) as resp:
            self.scr.handle()
        self.assertEqual( resp.exception.status_code, 404)


class TestCollectionServiceRequestOther( _TestSCR):
    def test_method_not_implemented(self):
        self._make( 'DELETE')
        with self.assertRaises( bottle.HTTPError) as resp:
            self.scr.handle()
        self.assertEqual( resp.exception.status_code, 405)
        self.assertEqual( set( resp.exception.headers['Allow'].split(',')),
                set([ 'GET','POST','HEAD' ]))

    def test_method_head(self):
        self._make('HEAD')
        resp = self.scr.handle()
        self.assertEqual( resp, None)

    def test_list_filter(self):
        self._make( 'GET', GET = {
            'mpm': 'prefork'
            })
        self.managed.list_resource_filter.return_value = [ 1, 2, 3 ]
        resp = self.scr.handle()
        self.assertListEqual( resp, ['/parent/p1/child/1',
            '/parent/p1/child/2',
            '/parent/p1/child/3'])
        self.managed.list_resource_filter.assert_called_once_with({
            'mpm' : 'prefork'
            })

    def test_get_all(self):
        self._make( 'GET', GET = {
            'getall': ''
            })
        self.scr.handle()
        self.managed.get_all_resources.assert_called_once_with()

    def test_method_create(self):
        self._make( 'POST', data={
            'lol': 1, 'blabla' : True
            })
        resp = self.scr.handle()
        self.managed.unserialize.assert_called_once_with({ 'lol': 1, 'blabla' :True })
        self.managed.validate.assert_called_once_with(self.managed.unserialize.return_value, for_edit=False)
        self.managed.create_resource.assert_called_once_with(
                self.managed.validate.return_value)
        self.assertEqual( resp.status_code, 201)
        self.assertEqual( resp.headers['Location'], '/parent/p1/child/blue')

    def test_method_create_escape(self):
        self._make( 'POST', data={
            'lol': 1,
            'blabla' : True
            })
        self.managed.create_resource.return_value = 'lol / mpm'
        resp = self.scr.handle()
        self.assertEqual( resp.headers['Location'], '/parent/p1/child/lol%20%2F%20mpm')

class _TestSRR( _Test):
    def _make( self, method, **kw):
        super( _TestSRR, self)._make( method, **kw)
        self.srr = ServiceResourceRequest([ 'p1', 'c2' ], self.cs)

class TestServiceResourceRequest( _TestSRR):
    def setUp(self):
        self._make( 'GET', GET={ })
        self.Managed.return_value.get_resource.return_value = { 'lol' : 1, 'blabla' : 'ping' }

    def test_get(self):
        self.manager.validate_id.side_effect = lambda y:y
        self.managed.validate_id.side_effect = lambda y:y
        s = self.srr.handle()
        self.assertDictEqual( s, {
            'lol' : 1, 'blabla' : 'ping'
            })
        self.manager.get_resource.assert_called_once_with( 'p1')
        self.managed.get_resource.assert_called_once_with( 'c2' )

    def test_get_configure(self):
        self.srr.handle()

        self.manager.configure.assert_called_once_with( self.fcs_conf)
        self.managed.configure.assert_called_once_with( self.cs_conf)

    def test_serialize(self):
        self.srr.handle()
        self.managed.serialize.assert_called_once_with({
            'lol' : 1, 'blabla' : 'ping'
            })


class TestServiceResourceRequestOther( _TestSRR):
    def test_method_head(self):
        self._make('HEAD')
        resp = self.srr.handle()
        self.assertEqual( resp, None)

    def test_method_put(self):
        self._make('PUT', data = { 'lol' : 1, 'blabla': 'ab' })
        self.manager.validate_id.side_effect = lambda y:y
        self.managed.validate_id.side_effect = lambda y:y
        self.srr.handle()
        self.managed.unserialize.assert_called_once_with({ 'lol': 1, 'blabla' : 'ab' })
        self.managed.validate.assert_called_once_with(self.managed.unserialize.return_value, for_edit=True)
        self.managed.modify_resource.assert_called_once_with( 'c2', self.managed.validate.return_value)

class TestServiceActionRequest( _Test):
    def setUp( self):
        self._make( 'POST' )
        self.sar = ServiceActionRequest([ 'p1', 'c2' ], self.cs, 'action')

        self.manager.validate_id.side_effect = lambda y:y
        self.managed.validate_id.side_effect = lambda y:y

    def _action(self, fn):
        manager = self.managed
        manager.action = types.MethodType( action(fn), manager, manager.__class__)

    def test_post_noarg(self):
        self.request.data = {}
        @self._action
        def callback(self, r):
            self.assertEqual( r, self.managed.get_resource.return_value)
            return 1

        resp = self.sar.handle()
        self.assertEqual( resp, 1)
        self.manager.get_resource.assert_called_once_with( 'p1')
        self.managed.get_resource.assert_called_once_with( 'c2' )


    def test_post_args(self):
        self.request.data = { 'a' : 2 }
        @self._action
        def callback(self, r, a):
            self.assertEqual( r, self.managed.get_resource.return_value)
            return a

        resp = self.sar.handle()
        self.assertEqual( resp, 2)

    def test_post_args_missing(self):
        self.request.data = {}
        @self._action
        def callback(self, r, a):
            return a
        self.assertRaises( bottle.HTTPError, self.sar.handle)

    def test_post_optional_missing(self):
        self.request.data = {}
        @self._action
        def callback(self, r, a=123):
            return a

        resp = self.sar.handle()
        self.assertEqual( resp, 123)

    def test_post_optional(self):
        self.request.data = { 'a' : 234 }
        @self._action
        def callback(self, r, a=123):
            return a

        resp = self.sar.handle()
        self.assertEqual( resp, 234)

