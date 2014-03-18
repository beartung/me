#!/usr/bin/python
# -*- coding: utf-8 -*-

from quixote.errors import TraversalError

from webapp.models.card import Card
from webapp.models.consts import Cate
from webapp.models.blog import Blog

_q_exports = []

def _q_lookup(req, name):
    if not req.user:
        raise TraversalError("need login")
    if not ('-' in name and name.lower()[-4:] in ['.mp3']):
        raise TraversalError("no such audio")
    n = name[:-4]
    ftype = name[-3:]
    target_id, audio_id, cate = n.split('-')
    if target_id.startswith('b'):
        blog = Blog.get(target_id.replace('b', ''))
        if blog:
            data = blog.audio_data(cate)
    if not data:
        raise TraversalError("no such audio")
    resp = req.response
    resp.set_content_type('audio/mp3')
    resp.set_header('Cache-Control', 'max-age=%d' % (365*24*60*60))
    resp.set_header('Expires', 'Wed, 01 Jan 2020 00:00:00 GMT')
    if 'pragma' in resp.headers:
        del resp.headers['pragma']
    if cate == Cate.ORIGIN:
        resp.set_content_type('application/force-download')
        resp.set_header('Content-Disposition', 'attachment; filename="%s.%s"' % (name, ftype));
    return data
