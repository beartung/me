#!/usr/bin/python
# -*- coding: utf-8 -*-
from quixote.errors import TraversalError, AccessError
from libs.template import st, stf

_q_exports = []


def _q_index(req):
    return "Hello Me!"
