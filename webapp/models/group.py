# models.group
# -*- coding: UTF-8 -*-

from quixote.html import html_quote
from operator import itemgetter, attrgetter
from wand.image import Image
from config import DEVELOP_MODE, SITE
from datetime import datetime, timedelta
from libs import doubandb, doubanfs, cache, doubanmc, store, User
from webapp.models.consts import *
from webapp.models.notify import Notify
from webapp.models.utils import scale, url_encode
from webapp.models.card import Card
from webapp.models.tag import Tag
import simplejson as json
import re

GROUP_UID_RE = re.compile('^[a-zA-z0-9_]+$')

class Group(object):

    FLAG_NORMAL = 'N'
    FLAG_DELETED = 'D'

    def __init__(self, id, uid, name, member_name, intro, photo_id, user_id, flag, n_tag, n_member, n_thread, ctime, rtime):
        self.id = str(id)
        self.uid = str(uid)
        self.name = name
        self.member_name = member_name
        self.intro = intro
        self.photo_id = photo_id
        self.user_id = str(user_id)
        self.flag = flag
        self.n_tag = n_tag
        self.n_member = n_member
        self.n_thread = n_thread
        self.ctime = ctime
        self.rtime = rtime

    @classmethod
    def is_valid_uid(cls, uid):
        if uid and len(uid) > 0:
            return GROUP_UID_RE.findall(uid)
        return False

    @classmethod
    def get(cls, id):
        r = store.execute("select id, uid, name, member_name, intro, photo, user_id, flag, n_tag,"
                " n_member, n_thread, ctime, rtime from me_group where id=%s and flag=%s", (id, cls.FLAG_NORMAL))
        if r and r[0]:
            return cls(*r[0])
        else:
            r = store.execute("select id, uid, name, member_name, intro, photo, user_id, flag, n_tag,"
                " n_member, n_thread, ctime, rtime from me_group where uid=%s and flag=%s", (id, cls.FLAG_NORMAL))
            if r and r[0]:
                return cls(*r[0])

    @classmethod
    def gets(cls):
        rs = store.execute("select id, uid, name, member_name, intro, photo, user_id, flag, n_tag,"
                " n_member, n_thread, ctime, rtime from me_group where flag=%s"
                " order by n_thread", cls.FLAG_NORMAL)
        return [cls(*r) for r in rs]

    @classmethod
    def new(cls, uid, user_id, name, member_name='', intro='', tags=[], filename=''):
        g = cls.get(uid)
        if not g:
            now = datetime.now()
            store.execute("insert into me_group(uid, user_id, name, member_name, intro, ctime, rtime)"
                " values(%s,%s,%s,%s,%s,%s,%s)", (uid, user_id, name, member_name, intro, now, now))
            store.commit()
            id = store.get_cursor(table="me_group").lastrowid
            g = cls.get(id)
            g.update_photo(filename)
            Notify.new(user_id, user_id, Notify.TYPE_CREATE_GROUP, extra={"group_id":g.id})
            g._join(user_id)
            g.update_tags(tags)
            return id

    def update_uid(self, uid):
        if uid != self.uid:
            g = Group.get(uid)
            if not g:
                store.execute("update me_group set uid=%s where id=%s", (uid, self.id))
                store.commit()

    def update(self, name, member_name, intro):
        store.execute("update me_group set name=%s, member_name=%s, intro=%s"
            " where id=%s", (name, member_name, intro, self.id))
        store.commit()

    def update_tags(self, tags):
        rs = store.execute("select tag_id from me_group_tag where group_id=%s and tagger_id=%s"
            " order by tag_id", (self.id, self.user_id))
        old_tag_ids = [str(r[0]) for r in rs]
        #print 'old tag ids', old_tag_ids
        store.execute("delete from me_group_tag where group_id=%s and tagger_id=%s", (self.id, self.user_id))
        for t in tags:
            if t:
                r = store.execute("select id from me_tag where name=%s", t)
                if r and r[0]:
                    tag_id = r[0][0]
                else:
                    store.execute("insert into me_tag(name) values(%s)", t)
                    tag_id = store.get_cursor(table="me_tag").lastrowid
                if tag_id:
                    store.execute("replace into me_group_tag(group_id, tagger_id, tag_id)"
                        " values(%s,%s,%s)", (self.id, self.user_id, tag_id))

        store.commit()
        for t in self.tag_names:
            ds = Card.gets_by_tag(t)
            [self._join(d.id) for d in ds]
            Notify.new(self.user_id, self.user_id, Notify.TYPE_TAG_ADD_GROUP, extra={"group_id":self.id, "tag":t})

    def update_photo(self, filename):
        data = open(filename).read()
        if len(data) > MAX_SIZE:
            return "too_large"
        store.execute("update me_group set `photo`=`photo`+1 where `id`=%s", self.id)
        store.commit()
        self.photo_id = self.photo_id + 1
        doubanfs.set("/me/g%s-%s-%s" % (self.id, self.photo_id, Cate.ORIGIN), data)
        o = scale(data, Cate.LARGE, DEFAULT_CONFIG)
        doubanfs.set("/me/g%s-%s-%s" % (self.id, self.photo_id, Cate.LARGE), o)
        for c in CATES[:2]:
            d = scale(o, c, DEFAULT_CONFIG)
            doubanfs.set("/me/g%s-%s-%s" % (self.id, self.photo_id, c), d)

    def photo_data(self, cate):
        if self.photo_id > 0:
            return doubanfs.get("/me/g%s-%s-%s" % (self.id, self.photo_id, cate))

    @property
    def icon(self):
        if self.photo_id > 0:
            return "/p/g%s-%s-%s.jpg" % (self.id, self.photo_id, Cate.ICON)
        return ''

    @property
    def m_name(self):
        return self.member_name or '成员'

    @property
    def rec_name(self):
        return self.name

    @property
    def photo(self):
        if self.photo_id > 0:
            return "/p/g%s-%s-%s.jpg" % (self.id, self.photo_id, Cate.LARGE)
        return ''

    @property
    def path(self):
        return "/group/%s/" % self.uid

    @property
    def url(self):
        return "%s/group/%s/" % (SITE, self.uid)

    @property
    def html_intro(self):
        return url_encode(self.intro)

    def dynamic_photo(self, x, y, scale='center-crop'):
        s = 'fs'
        if scale == 'center-crop':
            s = 'cc'
        return "/p/g%s-%s-r_%s_%sx%s.jpg" % (self.id, self.photo_id, s, x, y)

    def threads(self, start=0, limit=20):
        return Thread.gets_by_group(self.id)

    @property
    def tags(self):
        return Tag.get_group_tags(self.id)

    @property
    def tag_names(self):
        return [t.name for t in self.tags]

    @property
    def owner(self):
        return User(self.user_id)

    @property
    def owner_card(self):
        return Card.get(self.user_id)

    @property
    def members(self):
        rs = store.execute("select user_id from me_group_member where group_id=%s order by rtime desc", self.id)
        return [Card.get(r[0]) for r in rs]

    @classmethod
    def gets_by_card(cls, card_id):
        rs = store.execute("select group_id from me_group where user_id=%s", card_id)
        gs = [cls.get(r[0]) for r in rs]
        return [g for g in gs if not g.is_deleted]

    def remove(self):
        store.execute("update me_group set flag=%s where id=%s", (self.FLAG_DELETED, self.id))
        store.commit()

    @property
    def is_deleted(self):
        return self.flag == self.FLAG_DELETED

    def can_edit(self, user_id):
        return self.user_id == user_id

    def is_joined(self, user_id):
        r = store.execute("select 1 from me_group_member where"
            " group_id=%s and user_id=%s", (self.id, user_id))
        if r and r[0][0]:
            return True
        return False

    def add_member(self, user_id, by_id):
        self._join(user_id)
        Notify.new(user_id, by_id, Notify.TYPE_ADD_GROUP, extra={"group_id":self.id})

    def join(self, user_id):
        self._join(user_id)
        Notify.new(user_id, user_id, Notify.TYPE_JOIN_GROUP, extra={"group_id":self.id})

    def _join(self, user_id):
        if not self.is_joined(user_id):
            store.execute("insert into me_group_member(group_id, user_id)"
                " values(%s, %s)", (self.id, user_id))
            store.execute("update me_group set n_member=n_member+1, rtime=rtime"
                " where id=%s", self.id)
            store.commit()

    def quit(self, user_id):
        if self.is_joined(user_id):
            store.execute("delete from me_group_member where group_id=%s"
                " and user_id=%s", (self.id, user_id))
            store.execute("update me_group set n_member=n_member-1, rtime=rtime"
                " where id=%s", self.id)
            store.commit()

class Thread(object):

    FLAG_NORMAL = 'N'
    FLAG_DELETED = 'D'

    def __init__(self, id, title, group_id, author_id, flag, rtime):
        self.id = str(id)
        self.title = title
        self.group_id = str(group_id)
        self.author_id = str(author_id)
        self.flag = flag
        self.rtime = rtime
        from webapp.models.blog import Blog
        self.blog = Blog.get(self.id)

    def __getattr__(self, name):
        return getattr(self.blog, name)

    @classmethod
    def new(cls, user_id, group_id, title, content, filename, ftype):
        from webapp.models.blog import Blog
        id = Blog.new(user_id, Blog.TYPE_THREAD, content=content, filename=filename, ftype=ftype)
        if id:
            store.execute("insert into me_thread(id, title, group_id, author_id)"
                    " values(%s,%s,%s,%s)", (id, title, group_id, user_id))
            store.execute("update me_group set `n_thread`=`n_thread`+1, rtime=rtime where id=%s", group_id)
            store.commit()
            Notify.new(user_id, user_id, Notify.TYPE_NEW_THREAD, extra={"thread_id":id})
            return id

    @classmethod
    def get(cls, id):
        r = store.execute("select id, title, group_id, author_id, flag, rtime"
                " from me_thread where id=%s and flag=%s", (id, cls.FLAG_NORMAL))
        if r and r[0]:
            return cls(*r[0])

    @classmethod
    def gets_by_group(cls, group_id):
        rs = store.execute("select id, title, group_id, author_id, flag, rtime"
                " from me_thread where group_id=%s and flag=%s order by rtime desc", (group_id, cls.FLAG_NORMAL))
        return [cls(*r) for r in rs]

    @property
    def group(self):
        return Group.get(self.group_id)

    @property
    def path(self):
        return "/thread/%s/" % self.id

    @property
    def url(self):
        return "%s/thread/%s/" % (SITE, self.id)

    @classmethod
    def remove(cls, id, user_id):
        store.execute("update me_thread set flag=%s where `id`=%s and user_id=%s", (cls.FLAG_DELETED, id, user_id))
        store.commit()

    @property
    def rec_name(self):
        return self.title
