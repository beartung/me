# coding: utf-8

from os import path

SITE_DIR = path.dirname(path.abspath(__file__))

SITE = "http://me.xx.com"

MAKO_FS_CHECK = True

UPLOAD_DIR = path.join('/tmp', 'quixote_upload')

try:
    from local_config import *
except ImportError:
    pass
