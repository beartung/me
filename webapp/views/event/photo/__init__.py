#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson as json
import random
from functools import wraps
from quixote.errors import TraversalError, AccessError
from libs.template import st
from config import DEVELOP_MODE

from webapp.views import check_access
from webapp.models.card import Card
from webapp.models.consts import CITYS, ADMINS
from webapp.models.event import Event, EventPhoto

_q_exports = []

@check_access
def _q_lookup(req, name):
    photo = EventPhoto.get(name)
    if photo and photo.event:
        return PhotoUI(req, photo)
    return TraversalError("no such photo")


class PhotoUI(object):
    _q_exports = ['remove', 'rotate']

    def remove(self, req):
        if req.user and self.photo.can_remove(req.user.id):
            self.photo.remove()
        return req.redirect(self.event.path)

    def rotate(self, req):
        if req.get_method() == "POST":
            if req.user and self.photo.can_edit(req.user.id):
                rotate_left = req.get_form_var("rotate_left", None)
                rotate_right = req.get_form_var("rotate_right", None)
                if rotate_left:
                    self.photo.rotate("left")
                elif rotate_right:
                    self.photo.rotate("right")
        return req.redirect(self.photo.path)

    def __init__(self, req, photo):
        self.photo = photo
        self.event = photo.event

    def _q_index(self, req):
        event = self.event
        photo = self.photo
        index = event.photo_ids.index(photo.id)
        prev_id = -1
        next_id = -1
        total = len(event.photo_ids)
        first_id = event.photo_ids[0]
        if index > 0:
            prev_id = event.photo_ids[index - 1]
        elif total > 0:
            prev_id = event.photo_ids[-1]
        if index < total - 1:
            next_id = event.photo_ids[index + 1]
        elif total > 0:
            next_id = event.photo_ids[0]
        return st('/event/photo.html', **locals())
