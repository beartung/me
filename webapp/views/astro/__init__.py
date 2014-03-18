#!/usr/bin/python
# -*- coding: utf-8 -*-

from webapp.models.card import Card
from libs.template import st
from webapp.views import check_access

_q_exports = []

@check_access
def _q_lookup(req, name):
    cards = Card.gets_by_astro(name)
    return st('/cards/astro.html', **locals())
