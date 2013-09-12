#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The root of the napix project.

.. data:: HOME

    The current HOME dir
"""

import os

HOME = ''


def find_home(name, file):
    """
    Finds the :data:`HOME` dir of napixd.

    *name* is the name of the daemon started.

    *file* is the location of the __init__.py of the project.
    The HOME is searched relatively to this file.
    """
    global HOME
    env = os.environ.get('NAPIXHOME')
    if env:
        HOME = env
        return HOME

    package_dir = os.path.dirname(file)
    site_package = os.path.realpath(os.path.join(os.path.dirname(file), '..'))

    if 'site-packages' in package_dir:
        # installed in a VENV
        HOME = os.path.join(os.path.expanduser('~'), '.' + name)
    else:
        HOME = site_package
    return HOME

find_home('napixd', __file__)


def get_file(path, create=True):
    """
    Returns an absolute path to *file* relatively to :data:`HOME`.

    *create* indicate if the **folders** are created.
    """
    dirname, filename = os.path.split(path)
    path = get_path(dirname, create)
    return os.path.join(path, filename)


def get_path(dirname='', create=True):
    """
    Returns an absolute path to *dirname* relatively to :data:`HOME`.
    The path always contains a trailing /.

    *create* indicate if the **folders** are created.
    """
    if not dirname:
        path = HOME
    else:
        path = os.path.abspath(os.path.join(HOME, dirname, ''))
    if create and not os.path.isdir(path):
        os.makedirs(path)
    return path
