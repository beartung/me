#!/usr/bin/python
# -*- coding: utf-8 -*-

from webapp.models.card import Card, Badage
from libs.template import st
from webapp.views import check_access

_q_exports = []

@check_access
def _q_lookup(req, name):
    badage = Badage.get_by_name(name)
    if badage:
        cards = Card.gets_by_badage(badage.id)
        return st('/cards/badage.html', **locals())
    return TraversalError("no such badage")
