#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson as json
from quixote.errors import TraversalError, AccessError
from libs.template import st

from webapp.models.card import Card
from webapp.models.utils import escape_path, unescape_path
from webapp.views import check_access

_q_exports = []

@check_access
def _q_lookup(req, tag):
    tag = unescape_path(tag)
    cards = Card.gets_by_tag(tag)
    return st('/cards/tag.html', **locals())
