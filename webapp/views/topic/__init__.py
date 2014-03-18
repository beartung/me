#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson as json
from quixote.errors import TraversalError, AccessError
from libs.template import st

from webapp.models.blog import Topic
from webapp.models.utils import escape_path, unescape_path
from webapp.views import check_access

_q_exports = []

@check_access
def _q_lookup(req, name):
    topic = Topic.get_by_name(name)
    if topic:
        return st('/blog/topic.html', **locals())
    raise TraversalError("no such topic")
