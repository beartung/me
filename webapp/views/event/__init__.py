#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson as json
import random
from functools import wraps
from quixote.errors import TraversalError, AccessError
from libs.template import st, stf
from config import DEVELOP_MODE

from webapp.views import check_access
from webapp.models.card import Card
from webapp.models.event import Event
from webapp.models.consts import CITYS, ADMINS

_q_exports = ["photo"]

def _q_access(req):
    req.nav = '/events'

@check_access
def _q_lookup(req, name):
    event = Event.get(name)
    if event:
        return EventUI(req, event)
    return TraversalError("no such event")

@check_access
def _q_index(req):
    name = req.get_form_var('name', '')
    content = req.get_form_var('content', '')
    online_date = req.get_form_var('online_date', '')
    upload_file = req.get_form_var("upload_file", None)
    user_ids = []
    extra = {}
    error = None
    if req.get_method() == "POST":
        if not name or not online_date or not upload_file:
            error = 'miss_args'
        if error is None:
            id = Event.new(req.user.id, name, content, online_date, user_ids, extra)
            event = Event.get(id)
            if upload_file:
                error = event.update_photo(upload_file.tmp_filename)
            if not error:
                return req.redirect(event.path)
    return st('/event/edit.html', **locals())

class EventUI(object):
    _q_exports = ['edit', 'upload']

    def __init__(self, req, event):
        self.event = event

    def upload(self, req):
        event = self.event
        if req.get_method() == "POST":
            for i in xrange(0, 5):
                upload_file = req.get_form_var("upload_file_%s" % i, None)
                if upload_file:
                    event.upload(req.user.id, upload_file.tmp_filename)
            return req.redirect(event.path)

        return st('/event/upload.html', **locals())

    def edit(self, req):
        event = self.event
        if req.user and event.can_edit(req.user.id):
            name = req.get_form_var('name', '') or event.name
            content = req.get_form_var('content', '') or event.content
            online_date = req.get_form_var('online_date', '') or event.online_date
            upload_file = req.get_form_var("upload_file", None)
            user_ids = []
            extra = {}
            error = None
            if req.get_method() == 'POST':
                if not name or not online_date:
                    error = 'miss_args'
                if error is None:
                    event.update(name, content, online_date, user_ids, extra)
                    if upload_file:
                        error = event.update_photo(upload_file.tmp_filename)
                    if not error:
                        return req.redirect(event.path)
            return st('/event/edit.html', **locals())
        return AccessError("not editors")

    def _q_index(self, req):
        event = self.event
        start = req.get_form_var('start')
        limit = req.get_form_var('count', 18)
        start = start and str(start).isdigit() and int(start) or 0
        limit = limit and str(limit).isdigit() and int(limit) or 0
        prefix = "/event/%s/?" % event.id
        total = event.photo_num
        return st('/event/event.html', **locals())
