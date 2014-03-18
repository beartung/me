#!/usr/bin/python
# -*- coding: utf-8 -*-

from operator import itemgetter, attrgetter
import simplejson as json
import random
from functools import wraps
from quixote.errors import TraversalError, AccessError
from libs.template import st, stf
from libs import check_user, send_fireworks, publish_channel_msg
from config import DEVELOP_MODE
from datetime import datetime

from webapp.models.card import Card
from webapp.models.dig import Dig
from webapp.models.badage import Badage, Award
from webapp.models.tag import Tag
from webapp.models.event import Event, EventPhoto
from webapp.models.consts import CITYS, ADMINS
from webapp.models.blog import Blog, Topic
from webapp.models.group import Group

_q_exports = [
    'about', 'mine', 'cardcase', 'timeline', 'notifications', 'discover',
    'search', 'login', 'make', 'a', 'p', 'j',
    'card', 'cards', 'test', 'ldap', 'admin', 'tags', 'dig',
    'tag', 'zodiac', 'astro', 'province', 'hometown', 'badage', 'hide', 'banned',
    'event', 'events', 'update', 'blog', 'topic','magic', 'group', 'groups', 'thread',
    'fireworks',
    ]

NAV_TABS = [
    ('/update', '广播动态',   'bullhorn', ''),
    ('/', '最新图片', 'dashboard', ''),
    ('/events', '事件',   'picture', ''),
    ('/groups', '群组',   'group', ''),
    ('/mine',     '我的卡片', 'credit-card', ''),
    #('/cardcase', '卡片夹',   'briefcase', ''),
    #('/dig', '花名榜',   'trophy', ''),
    ('/cards', '全部成员',   'th', ''),
    ('/timeline', '时间线',   'calendar', ''),
    #('/magic', '星座',   'magic', ''),
]

def fireworks(req):
    return st('/misc/fireworks.html', **locals())

def check_access(f):
    @wraps(f)
    def _(*a, **kw):
        req = a[0]
        if req.get_form_var('output') == 'json':
            return f(*a, **kw)
        print 'check_access ', req.user, req.get_path()
        if not req.user and req.get_path() not in ['/login', '/about']:
            return req.redirect('/login')
        if req.card and req.card.is_hide and not req.get_path() == '/hide':
            if not (req.user and req.user.id in ADMINS and req.get_form_var("f", None)):
                return req.redirect('/hide')
        #if req.card and not req.card.is_basic and not req.get_path() == '/banned':
        #    return req.redirect('/banned')
        return f(*a, **kw)
    return _

def _q_access(req):
    check_user(req)

@check_access
def hide(req):
    if not req.card.is_hide:
        return req.redirect('/mine')
    return st('/misc/hide.html', **locals())

def banned(req):
    if req.card.is_basic:
        return req.redirect('/mine')
    return st('/misc/banned.html', **locals())

def test(req):
    return st('/misc/test.html', **locals())

@check_access
def events(req):
    req.nav = '/events'
    events = Event.gets()
    return st('/event/events.html', **locals())

@check_access
def groups(req):
    req.nav = '/groups'
    groups = Group.gets()
    return st('/group/groups.html', **locals())

@check_access
def tags(req):
    req.nav = '/'
    all_tags = Tag.gets(count=0)
    return st('/tags.html', **locals())

@check_access
def admin(req):
    if req.user and req.user.id in ADMINS:
        if req.get_method() == "POST":
            hide_id = req.get_form_var("hide_id", "")
            card = Card.get(hide_id)
            if card:
                Card.hide(card.id, req.user.id)
            badage_id = req.get_form_var("badage_id", "")
            badage_name = req.get_form_var("badage_name", "")
            badage_intro = req.get_form_var("badage_intro", "")
            badage_icon = req.get_form_var("badage_icon", "")
            badage = None
            if badage_id:
                badage = Badage.get(badage_id)
            if badage_name and badage_intro and badage_icon:
                if badage:
                    badage.update(badage_name, badage_intro, badage_icon)
                else:
                    Badage.new(badage_name, badage_intro, badage_icon)
            badage_name = req.get_form_var("add_badage_name", "")
            badage = Badage.get_by_name(badage_name)
            if badage:
                badage_user_ids = req.get_form_var("badage_user_ids", "").strip().split()
                for u in badage_user_ids:
                    card = Card.get(u)
                    if card:
                        Badage.add(card.id, badage.id, req.user.id)

            award_badage_name = req.get_form_var("award_badage_name", "")
            award_sponsor = req.get_form_var("award_sponsor", "")
            award_num = req.get_form_var("award_num", "")
            award_vote_days = req.get_form_var("award_vote_days", "")
            if award_badage_name and award_num and award_vote_days:
                award_num = award_num.isdigit() and int(award_num) or 5
                award_vote_days = award_vote_days.isdigit() and int(award_vote_days) or 7
                Award.new(award_badage_name, award_sponsor, award_num, award_vote_days)
        badages = Badage.gets()
        awards = Award.gets()
        q_card = req.get_form_var("q_card", "")
        q_tag = req.get_form_var("q_tag", "")
        if q_card and q_tag:
            taggers = Tag.get_taggers(q_card, q_tag)
        return st('/misc/admin.html', **locals())
    raise AccessError("need admin")

@check_access
def search(req):
    req.nav = '/'
    q = req.get_form_var("q", None)
    cards = []
    if q:
        cards = Card.search(q)
    return st('/search.html', **locals())

@check_access
def timeline(req):
    req.nav = '/timeline'
    years = xrange(datetime.now().year - 1, 2005, -1)
    now_year = str(datetime.now().year)
    year = req.get_form_var("year", now_year)
    start = req.get_form_var('start')
    limit = req.get_form_var('count', 20)
    start = start and str(start).isdigit() and int(start) or 0
    limit = limit and str(limit).isdigit() and int(limit) or 0
    n, cards = Card.gets_by_time(year, start, 200)
    return st('/timeline.html', **locals())

@check_access
def magic(req):
    req.nav = '/magic'
    card = req.card
    zodiac_total, zodiac_dist = Dig.zodiac_distribution()
    astro_total, astro_dist = Dig.astro_distribution()
    province_total, province_dist = Dig.province_distribution()
    return st('/magic.html', **locals())

@check_access
def update(req):
    req.nav = '/update'
    start = req.get_form_var('start')
    limit = req.get_form_var('count', 20)
    cate = req.get_form_var('cate', 'b')
    topic_num, topics = Topic.gets()
    start = start and str(start).isdigit() and int(start) or 0
    limit = limit and str(limit).isdigit() and int(limit) or 0
    error = None
    prefix = "/update?cate=%s&" % cate
    print 'update', error, req.get_method(), req.get_method() == "POST"
    if req.get_method() == "POST":
        text = req.get_form_var("update_text", '').strip()
        upload_file = req.get_form_var("update_file", None)
        print 'post', text, upload_file
        if not text and not upload_file:
            error = "no_data"
        if error is None:
            filename = ''
            ftype = ''
            if upload_file:
                filename = upload_file.tmp_filename
                ftype = upload_file.content_type
            bid = Blog.new(req.user.id, Blog.TYPE_BLOG, content=text, filename=filename, ftype=ftype)
            blog = Blog.get(bid)
            for t in blog.topics:
                html = str(stf("/blog/utils.html", "blog_ui", b=blog, req=req))
                data = {
                        'html': html
                        }
                publish_channel_msg('me-topic-%s' % t.id, data)
            return req.redirect('%sstart=%s' % (prefix, start))

    total, blogs = Blog.gets(start=start, limit=limit, blog_type=cate)
    if req.get_form_var("output", None) == 'json':
        fireworks = req.get_form_var("fireworks", None)
        req.response.set_content_type('application/json; charset=utf-8')
        d = {
            'total':total,
            'start':start,
            'count':limit,
        }
        if fireworks:
            d['blogs'] = [b.fireworks_dict() for b in blogs]
        else:
            d['blogs'] = [b.json_dict(req.user) for b in blogs]
        return json.dumps(d)
    return st('/update.html', **locals())

def discover(req):
    return req.redirect('/')

@check_access
def dig(req):
    req.nav = '/dig'
    basic_result = Dig.basic_result()
    gossip_result = Dig.gossip_result()
    hometowns = Dig.all_hometowns()
    hot_tags = Tag.gets(count=3)
    score_cards = Card.gets_by_score()
    return st('/dig.html', **locals())

@check_access
def about(req):
    req.nav = '/about'
    return st('/about.html', **locals())

@check_access
def notifications(req):
    card = req.card
    return st('/notify.html', **locals())

@check_access
def cards(req):
    req.nav = '/cards'
    cate = req.get_form_var('cate', '')
    start = req.get_form_var('start')
    start = start and str(start).isdigit() and int(start) or 0
    limit = 32
    total, cards = Card.gets(cate, start, limit)
    prefix = "/cards?cate=%s&" % cate
    if req.get_form_var("output", None) == 'json':
        req.response.set_content_type('application/json; charset=utf-8')
        r = {
                "cards": [c.json_dict(req.user) for c in cards]
        }
        return json.dumps(r)
    return st('/cards/cards.html', **locals())

@check_access
def cardcase(req):
    req.nav = '/cardcase'
    start = req.get_form_var('start')
    start = start and start.isdigit() and int(start) or 0
    card = req.card
    limit = DEVELOP_MODE and 2 or 16
    total, cards = Card.gets_by_card(req.user.id, start, limit)
    return st('/cardcase.html', **locals())

@check_access
def _q_index(req):
    if req.card and not req.card.is_basic:
        return req.redirect('/mine')
    req.nav = '/'
    card = req.card
    photo_num, photo_cards = Card.gets(cate='photo', limit=20)

    all_badages = Badage.gets()

    num, blogs = Blog.gets(limit=30)
    num, photo_blogs = Blog.get_photo_blogs(limit=40)
    photo_blogs = [b for b in photo_blogs if b.n_unlike == 0]
    num, event_photos = EventPhoto.gets(limit=20)
    new_photos = sorted(photo_blogs + event_photos + photo_cards, key=attrgetter('sort_time'), reverse=True)
    return st('/index.html', **locals())

@check_access
def mine(req):
    req.nav = '/mine'
    card = None
    card = req.card
    if card and not card.is_basic:
        return make(req)
    n, blogs = Blog.gets(card.id, blog_type='b')
    award = Award.get_actived()
    return st('/home.html', **locals())

@check_access
def login(req):
    return st('/login.html', **locals())

@check_access
def make(req):
    req.nav = '/mine'
    error = None
    citys = CITYS
    email = req.get_form_var('email', '')
    skype = req.get_form_var('skype', '').strip()
    name = req.get_form_var('name', '')
    alias = req.get_form_var('alias', '')
    phone = req.get_form_var('phone', '')
    join_time = req.get_form_var('join_time', '')
    birthday = req.get_form_var('birthday', '')
    hometown = req.get_form_var('hometown', '')
    province = req.get_form_var('province', '')
    sex = req.get_form_var('sex', '0')
    love = req.get_form_var('love', '0')
    zodiac = req.get_form_var('zodiac', '0')
    astro = req.get_form_var('astro', '0')
    marriage = req.get_form_var('marriage', '0')
    weibo = req.get_form_var('weibo', '')
    instagram = req.get_form_var('instagram', '')
    blog = req.get_form_var('blog', '')
    github = req.get_form_var('github', '')
    code = req.get_form_var('code', '')
    resume = req.get_form_var('resume', '')
    intro = req.get_form_var('intro', '')
    upload_file = req.get_form_var("upload_file", None)
    tags = req.get_form_var('tags', '').strip()
    if len(tags) > 0:
        tags = tags.split()
    else:
        tags = []
    card = req.card
    profile = card.profile
    #print sex, love, zodiac, astro, birthday, marriage, province, hometown, weibo, instagram, code, github, resume, intro
    if req.user and req.get_method() == 'POST':
        print 'check', email, skype, name, phone, join_time
        card.update_basic(name, skype, alias, join_time)
        card.tag(req.user.id, tags)
        if upload_file:
            error = card.update_photo(upload_file.tmp_filename)
        card.update_profile(sex, love, zodiac, astro, birthday, marriage, province, hometown,
                weibo, instagram, blog, code, github, resume, intro)
        if not error:
            return req.redirect("/mine")
    return st('/card/edit.html', **locals())
