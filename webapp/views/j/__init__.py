#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson as json
from quixote.errors import TraversalError, AccessError
from libs.template import st, stf
from datetime import datetime
from operator import itemgetter, attrgetter
from webapp.models.card import Card, Notify, Comment
from webapp.models.badage import Award
from webapp.models.consts import Cate
from webapp.models.question import Question, Answer
from webapp.models.card import Card
from webapp.models.utils import get_users_dict
from webapp.models.event import EventPhoto, Event
from webapp.models.group import Group
from webapp.models.blog import Rec

_q_exports = ['like', 'read_notify', 'tag', 'comment', 'uncomment', 'request_photo', 'timeline',
    'request_change_photo', 'card', 'blog', 'vote', 'ask', 'event', 'names', 'rec']

def _q_access(req):
    req.response.set_content_type('application/json; charset=utf-8')

def card(req):
    card_id = req.get_form_var('cid', '')
    card = Card.get(card_id)
    if card:
        return json.dumps(card.json_dict(req.user))
    raise TraversalError('no such card')

def read_notify(req):
    r = {
        'err':'ok'
    }
    if req.get_method() == "POST":
        if req.user:
            blog_id = req.get_form_var('bid', None)
            if blog_id:
                Notify.read_by_blog(req.user.id, blog_id)
            else:
                Notify.read_by_card(req.user.id)
            card = Card.get(req.user.id)
            r['num'] = card and card.notify_num or 0
    return json.dumps(r)

def like(req):
    r = {
        'err':'invalid'
    }
    if req.get_method() == "POST":
        card_id = req.get_form_var('cid', '')
        card = Card.get(card_id)
        if card and req.user and not card.is_liked(req.user.id):
            card.like(req.user.id)
            card = Card.get(card.id)
            r = {
                'err':'ok',
                'inner_html': stf("/card/card.html", "card_likers", card=card, req=req),
                'like_num': card.like_num,
            }
    return json.dumps(r)

def vote(req):
    r = {
        'err':'invalid'
    }
    if req.get_method() == "POST":
        card_id = req.get_form_var('cid', '')
        aid = req.get_form_var('aid', '')
        card = Card.get(card_id)
        award = Award.get(aid)
        if card and req.user and award and \
            not award.is_expired and not award.is_voted(card.id, req.user.id):
            award.vote_by_user(card.id, req.user.id)
            r = {
                'err':'ok',
            }
    return json.dumps(r)

def request_photo(req):
    r = {
        'err':'invalid'
    }
    if req.get_method() == "POST":
        card_id = req.get_form_var('cid', '')
        card = Card.get(card_id)
        if card and req.user:
            Notify.new(card.id, req.user.id, Notify.TYPE_REQUEST_PHOTO)
            r = {
                'err':'ok',
            }
    return json.dumps(r)

def request_change_photo(req):
    r = {
        'err':'invalid'
    }
    if req.get_method() == "POST":
        card_id = req.get_form_var('cid', '')
        card = Card.get(card_id)
        if card and req.user:
            Notify.new(card.id, req.user.id, Notify.TYPE_REQUEST_CHANGE_PHOTO)
            r = {
                'err':'ok',
            }
    return json.dumps(r)

def tag(req):
    r = {
        'err':'invalid'
    }
    tags = req.get_form_var('tags', '').strip()
    if len(tags) > 0:
        tags = tags.split()
    else:
        tags = []
    if req.get_method() == "POST":
        cate = req.get_form_var('cate', '')
        card_id = req.get_form_var('cid', '')
        #print 'j tags', card_id, tags
        card = Card.get(card_id)
        if card and req.user and tags:
            card.tag(req.user.id, tags)
            card = Card.get(card.id)
            tmpl_func = 'card_tags'
            if cate == 'small':
                tmpl_func = 'small_card_tags'
            r = {
                'err':'ok',
                'inner_html': stf('/card/utils.html', tmpl_func, card=card, req=req)
            }
    return json.dumps(r)

def comment(req):
    r = {
        'err':'invalid'
    }
    if req.get_method() == "POST":
        card_id = req.get_form_var('cid', '')
        card = Card.get(card_id)
        content = req.get_form_var('content', '').strip()
        #print 'j comment', card_id, content
        if card and req.user and content:
            card.comment(req.user.id, content)
            card = Card.get(card.id)
            r = {
                'err':'ok',
                'html': stf("/card/card.html", "card_comments", card=card, req=req),
            }
    return json.dumps(r)

def uncomment(req):
    r = {
        'err':'invalid'
    }
    if req.get_method() == "POST":
        card_id = req.get_form_var('cid', '')
        comment_id = req.get_form_var('comment_id', '')
        card = Card.get(card_id)
        #print 'j uncomment', comment_id
        if req.user and card:
            Comment.remove(req.user.id, comment_id)
            card = Card.get(card.id)
            r = {
                'err':'ok',
                'html': stf("/card/card.html", "card_comments", card=card, req=req),
            }
    return json.dumps(r)

def timeline_object(o):
    ret = {}
    if isinstance(o, Card):
        card = o
        intro = ''
        if card.profile.intro:
            intro = '<i class="icon-quote-left"></i>%s<i class="icon-quote-right"></i>' % card.profile.intro
        ret = {
            "startDate": card.join_time.strftime('%Y,%m,%d'),
            "headline": "<a href=\"%s\">%s</a> 加入豆瓣" % (card.path, card.screen_name),
            "tag": ' '.join(card.tags),
            "text": intro,
            "asset": {
                "media": card.photo,
                "thumbnail": card.owner.picture() or '',
                #"credit": card.name,
                "caption": ' '.join([t.name for t in card.ptags]),
            }
        }
    elif isinstance(o, Event):
        event = o
        intro = ''
        if event.content:
            intro = '<i class="icon-quote-left"></i>%s<i class="icon-quote-right"></i>' % event.content
        ret = {
            "startDate": event.online_date.strftime('%Y,%m,%d'),
            "headline": "<a href=\"%s\">%s</a>" % (event.path, event.name),
            "text": intro,
            "asset": {
                "media": event.cover(),
                "thumbnail": event.cover(Cate.ICON) or '',
            }
        }
    return ret

def get_sorted_objects():
    cards = Card.gets_all()
    events = Event.gets()
    objects = sorted(cards + events, key=attrgetter('sort_date'))
    return objects

def timeline(req):
    r = {}
    objects = get_sorted_objects()
    date = [timeline_object(o) for o in objects]
    r["timeline"] = {
        "headline":"豆瓣花名册",
        "type":"default",
        "text":"As Time Goes By",
        "startDate":"2005,3,6",
        "asset": {
            "media": "/static/img/bo.jpg",
            "caption": "2005年3月6日 阿北 豆瓣胡同 星巴克",
        },
        "date": date,
    }
    return json.dumps(r)

def ask(req):
    r = {
        'err':'invalid'
    }
    if req.get_method() == "POST":
        card_id = req.get_form_var('cid', '')
        card = Card.get(card_id)
        content = req.get_form_var('content', '').strip()
        anonymous = req.get_form_var('anonymous', None)
        if card and req.user and content and req.user.id != card.id:
            qid = Question.new(card.id, req.user.id, content, anonymous == '1')
            card = Card.get(card.id)
            r = {
                'err':'ok',
                'html': stf("/card/card.html", "card_answers", card=card, req=req),
            }
    return json.dumps(r)

def names(req):
    q = req.get_form_var('term', None)
    q = q.strip()
    r = []
    if q:
        user_dict = get_users_dict()
        ids = set([v for k, v in user_dict.iteritems() if k.startswith(q)])
        for i in list(ids):
            card = Card.get(i)
            r.append({ "id": card.id, "label":card.screen_name , "value": card.uid})
    return json.dumps(r)


def rec(req):
    r = {
        'err':'invalid'
    }
    rec_type = req.get_form_var('type', None)
    rec_id = req.get_form_var('id', None)
    if rec_type and rec_id and req.get_method() == 'POST' and req.user:
        rid = Rec.new(req.user.id, rec_type, rec_id)
        if rid:
            r = { 'err':'ok', }
    return json.dumps(r)
