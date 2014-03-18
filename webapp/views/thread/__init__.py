#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson as json
from quixote.errors import TraversalError, AccessError
from libs.template import st, stf

from webapp.models.group import Thread
from webapp.views import check_access

_q_exports = []

@check_access
def _q_lookup(req, id):
    thread = Thread.get(id)
    if thread:
        return ThreadUI(req, thread)
    return TraversalError("no such thread")


class ThreadUI(object):
    _q_exports = ['remove']

    def __init__(self, req, thread):
        self.thread = thread

    def _q_index(self, req):
        thread = self.thread
        return st('/thread/thread.html', **locals())

    def remove(self, req):
        if req.user and req.user.id == self.thread.user_id:
            group = self.thread.group
            Thread.remove(self.thread.id, req.user.id)
            return req.redirect("/")
        return AccessError("need permission")
