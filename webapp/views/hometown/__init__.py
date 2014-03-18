#!/usr/bin/python
# -*- coding: utf-8 -*-

from webapp.models.card import Card
from webapp.views import check_access
from libs.template import st

_q_exports = []

@check_access
def _q_lookup(req, name):
    cards = Card.gets_by_hometown(name)
    return st('/cards/hometown.html', **locals())
