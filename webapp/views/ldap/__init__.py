#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson as json
from quixote.errors import TraversalError, AccessError
from libs.template import st, stf
from webapp.models.card import Card
from webapp.views import check_access
from webapp.views.card import CardUI

_q_exports = []

def _q_lookup(req, name):
    card = Card.get_by_ldap(name)
    if card and not card.is_hide:
        return CardUI(req, card)
    return TraversalError("no such card")
