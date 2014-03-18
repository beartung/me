#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson as json
from quixote.errors import TraversalError, AccessError
from libs.template import st, stf

from webapp.models.card import Card
from webapp.models.blog import Blog
from webapp.models.question import Answer
from webapp.models.badage import Award
from webapp.views import check_access

_q_exports = []

@check_access
def _q_lookup(req, id):
    card = Card.get(id)
    if card:
        if card.is_hide:
            return st('/misc/hide.html', **locals())
        return CardUI(req, card)
    return TraversalError("no such card")


class CardUI(object):
    _q_exports = ['like', 'comment', 'tag', 'blogs', 'answer']

    def __init__(self, req, card):
        self.card = card

    def blogs(self, req):
        start = req.get_form_var('start')
        start = start and str(start).isdigit() and int(start) or 0
        limit = 20
        error = None
        card = self.card
        prefix = "%sblogs?" % card.path
        total, blogs = Blog.gets(card_id=self.card.id, start=start, limit=limit, blog_type='b')
        return st('/blog/blogs.html', **locals())

    def _q_index(self, req):
        card = self.card
        if req.get_form_var("output", None) == 'json':
            req.response.set_content_type('application/json; charset=utf-8')
            return json.dumps(card.json_dict(req.user))
        elif req.get_form_var("html_widget", None):
            return stf("/card/utils.html", "card_widget", card=card, req=req)
        n, blogs = Blog.gets(card.id, blog_type='b')
        return st('/card/card.html', **locals())

    def like(self, req):
        card = self.card
        if req.user and not card.is_liked(req.user.id):
            card.like(req.user.id)
        return st('/card/card.html', **locals())

    def comment(self, req):
        card = self.card
        content = req.get_form_var('content', '').strip()
        if req.user and req.get_method() == 'POST' and content:
            card.comment(req.user.id, content)
        return req.redirect(card.path)

    def tag(self, req):
        card = self.card
        tags = req.get_form_var('tags', '').strip()
        if len(tags) > 0:
            tags = tags.split()
        else:
            tags = []
        if req.user and req.get_method() == 'POST' and tags:
            card.tag(req.user.id, tags)
        return req.redirect(card.path)

    def answer(self, req):
        card = self.card
        if req.user and req.user.id == card.id and req.get_method() == 'POST':
            text = req.get_form_var("update_text", '').strip()
            upload_file = req.get_form_var("update_file", None)
            question_id = req.get_form_var("question_id", None)
            filename = ''
            ftype = ''
            if upload_file:
                filename = upload_file.tmp_filename
                ftype = upload_file.content_type
            if (text or filename) and question_id:
                Answer.new(question_id, req.user.id, text, filename=filename, ftype=ftype)
        return req.redirect(card.path)
