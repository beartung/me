#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson as json
from quixote.errors import TraversalError, AccessError
from libs.template import st, stf

from webapp.models.group import Group, Thread
from webapp.models.card import Card
from webapp.views import check_access

_q_exports = []

@check_access
def _q_lookup(req, id):
    g = Group.get(id)
    if g:
        return GroupUI(req, g)
    return TraversalError("no such group")

def _q_access(req):
    req.nav = '/groups'

@check_access
def _q_index(req):
    uid = req.get_form_var('uid', '').strip()
    name = req.get_form_var('name', '')
    member_name = req.get_form_var('member_name', '')
    intro = req.get_form_var('intro', '')
    upload_file = req.get_form_var("upload_file", None)
    tags = req.get_form_var('tags', '').strip()
    error = None
    if req.user and req.get_method() == 'POST':
        if not uid or not name or not intro or not upload_file:
            error = 'miss_args'
        elif not Group.is_valid_uid(uid):
            error = 'uid_invalid'
        elif Group.get(uid):
            error = 'uid_exists'
        if error is None:
            if len(tags) > 0:
                tags = tags.split()
            else:
                tags = []
            id = Group.new(uid, req.user.id, name, member_name, intro, tags, upload_file.tmp_filename)
            return req.redirect('/group/%s/' % uid)
    return st('/group/edit.html', **locals())

class GroupUI(object):
    _q_exports = ['edit', 'join', 'quit', 'add_member', 'new_thread']

    def __init__(self, req, group):
        self.group = group

    def _q_index(self, req):
        group = self.group
        return st('/group/group.html', **locals())

    def join(self, req):
        group = self.group
        if req.user and not group.is_joined(req.user.id):
            group.join(req.user.id)
        return req.redirect(group.path)

    def add_member(self, req):
        group = self.group
        q = req.get_form_var('q', None)
        if q and req.get_method() == 'POST':
            card = Card.get(q)
            if not card:
                card = Card.get_by_ldap(q)
            if card:
                group.add_member(card.id, req.user.id)
        return req.redirect(group.path)

    def quit(self, req):
        group = self.group
        if req.user and group.is_joined(req.user.id):
            group.quit(req.user.id)
        return req.redirect(group.path)

    def edit(self, req):
        group = self.group
        uid = req.get_form_var('uid', '').strip()
        name = req.get_form_var('name', '')
        member_name = req.get_form_var('member_name', '')
        intro = req.get_form_var('intro', '')
        upload_file = req.get_form_var("upload_file", None)
        tags = req.get_form_var('tags', '').strip()
        error = None
        if req.user and req.get_method() == 'POST':
            if uid:
                if not Group.is_valid_uid(uid):
                    error = 'uid_invalid'
                elif Group.get(uid):
                    error = 'uid_exists'
                else:
                    group.update_uid(uid)
            if name and member_name and intro:
                group.update(name, member_name, intro)
            if len(tags) > 0:
                tags = tags.split()
            else:
                tags = []
            group.update_tags(tags)
            group = Group.get(group.id)
            return req.redirect(group.path)
        return st('/group/edit.html', **locals())

    def new_thread(self, req):
        group = self.group
        thread_title = req.get_form_var("title", '').strip()
        text = req.get_form_var("update_text", '').strip()
        upload_file = req.get_form_var("update_file", None)
        error = None
        if req.get_method() == "POST" and req.user:
            if not thread_title or not text:
                error = "no_data"
            if error is None:
                filename = ''
                ftype = ''
                if upload_file:
                    filename = upload_file.tmp_filename
                    ftype = upload_file.content_type
                id = Thread.new(req.user.id, group.id, thread_title, text, filename, ftype)
                if id:
                    return req.redirect("/thread/%s/" % id)
        return st('/thread/create.html', **locals())
