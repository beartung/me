#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson as json
from webapp.models.consts import *
from webapp.views import check_access
from webapp.models.event import Event, EventPhoto, PhotoTag
from webapp.models.card import Card
from webapp.models.utils import get_users_dict
from quixote.errors import TraversalError, AccessError
from libs.template import st, stf

_q_exports = ['upload', 'remove_photo', 'comment_photo', 'like_photo', 'uncomment_photo', 'photo_tags',
        'add_photo_tag', 'remove_photo_tag']

def upload(req):
    r = {
        'err':'invalid'
    }
    eid = req.get_form_var("eid", None)
    if eid:
        e = Event.get(eid)
        if e and req.get_method() == "POST" and req.user:
            upload_file = req.get_form_var("upload_file", None)
            id = e.upload(req.user.id, upload_file.tmp_filename)
            if id:
                p = EventPhoto.get(id)
                r['err'] = 'ok'
                r['id'] = p.id
                r['url'] = p.url(Cate.SMALL)
    return json.dumps(r)

def remove_photo(req):
    r = {
        'err':'invalid'
    }
    eid = req.get_form_var("eid", None)
    pid = req.get_form_var("pid", None)
    e = Event.get(eid)
    p = EventPhoto.get(pid)
    if e and p and req.user.id and req.get_method() == "POST":
        p.remove()
        r['err'] = 'ok';
    return json.dumps(r)

def like_photo(req):
    r = {
        'err':'invalid'
    }
    if req.get_method() == "POST":
        photo_id = req.get_form_var('pid', '')
        photo = EventPhoto.get(photo_id)
        if photo and req.user:
            photo.like(req.user.id)
            photo = EventPhoto.get(photo.id)
            r = {
                'err':'ok',
                'html': stf("/event/photo.html", "photo_likers", photo=photo),
            }
    return json.dumps(r)

def comment_photo(req):
    r = {
        'err':'invalid'
    }
    if req.get_method() == "POST":
        photo_id = req.get_form_var('pid', '')
        photo = EventPhoto.get(photo_id)
        content = req.get_form_var('content', '').strip()
        if photo and req.user and content:
            photo.comment(req.user.id, content)
            photo = EventPhoto.get(photo.id)
            r = {
                'err':'ok',
                'html': stf("/event/photo.html", "photo_comments", photo=photo, req=req),
            }
    return json.dumps(r)

def uncomment_photo(req):
    r = {
        'err':'invalid'
    }
    if req.get_method() == "POST":
        photo_id = req.get_form_var('pid', '')
        comment_id = req.get_form_var('comment_id', '')
        photo = EventPhoto.get(photo_id)
        if photo and req.user:
            photo.uncomment(req.user.id, comment_id)
            photo = EventPhoto.get(photo.id)
            r = {
                'err':'ok',
                'html': stf("/event/photo.html", "photo_comments", photo=photo, req=req),
            }
    return json.dumps(r)

def photo_tags(req):
    r = {
        'err':'invalid'
    }
    photo_id = req.get_form_var('image-id', None)
    photo = EventPhoto.get(photo_id)
    if photo:
        tags = [t.json_dict(req.user) for t in photo.tags]
        r = {
                "Image" : [{"id":photo.id, "Tags":tags }],
                "options":{ "tag":{ "flashAfterCreation": True } }
            }
    return json.dumps(r)

def add_photo_tag(req):
    r = { 'result':False }
    photo_id = req.get_form_var('image_id', None)
    photo = photo_id and EventPhoto.get(photo_id)
    if photo and req.user:
        left = req.get_form_var('left', None)
        top = req.get_form_var('top', None)
        width = req.get_form_var('width', None)
        height = req.get_form_var('height', None)
        name = req.get_form_var('name', None)
        uid = req.get_form_var('name_id', None)
        if name and not uid:
            user_dict = get_users_dict()
            uid = user_dict.get(name.cstrip().lower(), None)
        if uid:
            card = Card.get(uid)
            if card:
                tid = PhotoTag.new(photo_id, card.id, req.user.id, left, top, width, height)
                tag = PhotoTag.get(tid)
                if tag:
                    r = {
                            "result":True,
                            "tag": tag.json_dict(req.user)
                        }
    return json.dumps(r)

def remove_photo_tag(req):
    r = { 'result':False }
    photo_id = req.get_form_var('image-id', None)
    tag_id = req.get_form_var('tag-id', None)
    photo = EventPhoto.get(photo_id)
    tag = PhotoTag.get(tag_id)
    if photo and tag and req.user:
        tag.remove(req.user.id)
        r = {"result":True, "message":"╮( ╯ 3 ╰ )╭"}
    return json.dumps(r)
