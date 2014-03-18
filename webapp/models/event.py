# models.card
# -*- coding: UTF-8 -*-

import re
from wand.image import Image
from datetime import datetime, timedelta
from libs import doubandb, doubanfs, Employee, cache, doubanmc, store, User
from webapp.models.consts import *
from webapp.models.utils import scale, url_encode
from webapp.models.card import Card, Notify
from config import SITE
import simplejson as json
import time

class Event(object):
    def __init__(self, id, author_id, name, content, photo_id, online_date, user_ids, extra, rtime):
        self.id = str(id)
        self.author_id = str(author_id)
        self.name = name
        self.content = content
        self.photo_id = photo_id
        self.online_date = online_date or ''
        self.user_ids = user_ids.strip().split()
        try:
            self.extra = json.loads(extra)
        except:
            extra = {}
        self.rtime = rtime

    @property
    def sort_date(self):
        return self.online_date

    def update(self, name, content, online_date, user_ids=[], extra={}):
        user_ids = ' '.join(user_ids)
        try:
            extra = json.dumps(extra)
        except:
            extra = "{}"
        store.execute("update me_event set name=%s, content=%s,"
            " online_date=%s, user_ids=%s, extra=%s where id=%s", (name, content, online_date,
                user_ids, extra, self.id))
        store.commit()

    def latest_comments(self, limit=10):
        rs = store.execute("select c.id, c.photo_id, c.author_id, c.content, c.rtime"
                " from me_event_photo as p, me_photo_comment as c"
                " where p.event_id=%s and p.id=c.photo_id order by c.rtime limit %s", (self.id, limit))
        return [PhotoComment(*r) for r in rs]

    @classmethod
    def new(cls, author_id, name, content, online_date, user_ids=[], extra={}):
        user_ids = ' '.join(user_ids)
        try:
            extra = json.dumps(extra)
        except:
            extra = "{}"
        store.execute("insert into me_event(author_id, name, content,"
            " online_date, user_ids, extra) values(%s,%s,%s,%s,%s,%s)", (author_id, name, content, online_date,
                user_ids, extra))
        store.commit()
        id = store.get_cursor(table="me_event").lastrowid
        return id

    def can_edit(self, user_id):
        return user_id in set(ADMINS + EDITORS) or user_id == self.author_id

    @classmethod
    def get(cls, id):
        r = store.execute("select id, author_id, name, content, photo, online_date, user_ids, extra, rtime"
            " from me_event where id=%s", id)
        if r:
            return cls(*r[0])

    @classmethod
    def gets(cls, sort='online'):
        if sort == 'new':
            rs = store.execute("select distinct(event_id) from me_event_photo order by rtime desc")
        else:
            rs = store.execute("select id from me_event order by online_date desc")
        return [cls.get(r[0]) for r in rs]

    def update_photo(self, filename):
        data = open(filename).read()
        if len(data) > MAX_SIZE:
            return "too_large"
        store.execute("update me_event set `photo`=`photo`+1 where `id`=%s", self.id)
        store.commit()
        self.photo_id = self.photo_id + 1
        doubanfs.set("/me/evc%s-%s-%s" % (self.id, self.photo_id, Cate.ORIGIN), data)
        o = scale(data, Cate.LARGE, DEFAULT_CONFIG)
        doubanfs.set("/me/evc%s-%s-%s" % (self.id, self.photo_id, Cate.LARGE), o)
        for c in CATES[:2]:
            d = scale(o, c, DEFAULT_CONFIG)
            doubanfs.set("/me/evc%s-%s-%s" % (self.id, self.photo_id, c), d)
        if self.photo_id == 1:
            from webapp.models.blog import Blog
            Blog.new(self.author_id, Blog.TYPE_BLOG, Blog.BLOG_EVENT, extra={'photo_id':self.photo_id, 'event_id':self.id})

    def photo_data(self, cate):
        if self.photo_id > 0:
            return doubanfs.get("/me/evc%s-%s-%s" % (self.id, self.photo_id, cate))

    def cover(self, cate=Cate.LARGE):
        if self.photo_id > 0:
            return "/p/evc%s-%s-%s.jpg" % (self.id, self.photo_id, cate)
        return ''

    def dynamic_cover(self, x, y, scale='center-crop'):
        if self.photo_id > 0:
            s = 'fs'
            if scale == 'center-crop':
                s = 'cc'
            return "/p/evc%s-%s-r_%s_%sx%s.jpg" % (self.id, self.photo_id, s, x, y)
        return ''

    @property
    def path(self):
        return "/event/%s/" % self.id

    @property
    def url(self):
        return "%s/event/%s/" % (SITE, self.id)

    @property
    def photo_ids(self):
        rs = store.execute("select id from me_event_photo where event_id=%s", self.id)
        return [str(r[0]) for r in rs]

    @property
    def photo_num(self):
        return len(self.photo_ids)

    @property
    def latest_photo(self):
        return self.photo_num > 0 and self.photos[0]

    @property
    def photos(self):
        rs = store.execute("select id from me_event_photo where event_id=%s order by id desc", self.id)
        return [EventPhoto.get(str(r[0])) for r in rs]

    @property
    def html_content(self):
        return url_encode(self.content)

    @property
    def owner(self):
        return User(id=self.author_id)

    @property
    def owner_card(self):
        return Card.get(self.author_id)

    @property
    def authors(self):
        rs = store.execute("select distinct(author_id) from me_event_photo where event_id=%s", self.id)
        return [User(id=str(r[0])) for r in rs]

    @property
    def author_cards(self):
        rs = store.execute("select distinct(author_id) from me_event_photo where event_id=%s", self.id)
        return [Card.get(str(r[0])) for r in rs]

    def upload(self, user_id, filename):
        return EventPhoto.new(self.id, user_id, filename)

class PhotoTag(object):
    def __init__(self, id, photo_id, user_id, author_id, left, top, width, height, rtime):
        self.id = str(id)
        self.user_id = str(user_id)
        self.photo_id = str(photo_id)
        self.author_id = str(author_id)
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.rtime = rtime

    @property
    def author(self):
        return User(id=self.author_id)

    @property
    def author_card(self):
        return Card.get(self.author_id)

    @property
    def card(self):
        return Card.get(self.user_id)

    @classmethod
    def new(cls, photo_id, user_id, author_id, left, top, width, height):
        store.execute("insert into me_photo_tag(photo_id,user_id,author_id,`left`,top,width,height)"
                " values(%s,%s,%s,%s,%s,%s,%s)", (photo_id, user_id, author_id, left, top, width, height))
        store.commit()
        id = store.get_cursor(table="me_photo_tag").lastrowid
        Notify.new(user_id, author_id, Notify.TYPE_PHOTO_TAG, extra={"photo_id":photo_id, "card_id":user_id})
        return id

    @classmethod
    def get(cls, id):
        r = store.execute("select id, photo_id, user_id, author_id, `left`, top, width, height, rtime"
                " from me_photo_tag where id=%s", id)
        if r:
            return cls(*r[0])

    @classmethod
    def gets_by_photo(cls, photo_id):
        rs = store.execute("select id, photo_id, user_id, author_id, `left`, top, width, height, rtime"
                " from me_photo_tag where photo_id=%s", photo_id)
        return [cls(*r) for r in rs]

    def remove(self, user_id):
        if user_id == self.author_id:
            store.execute("delete from me_photo_tag where id=%s", self.id)
            store.commit()

    def json_dict(self, user):
        ret = {}
        ret['id'] = self.id
        ret['text'] = self.card.screen_name
        ret['left'] = self.left
        ret['top'] = self.top
        ret['width'] = self.width
        ret['height'] = self.height
        ret['url'] = self.card.path
        ret['isDeleteEnable'] = user and user.id == self.author_id
        return ret

class EventPhoto(object):
    def __init__(self, id, event_id, author_id, rtime):
        self.id = str(id)
        self.event_id = str(event_id)
        self.author_id = str(author_id)
        self.rtime = rtime

    @classmethod
    def get(cls, id):
        r = store.execute("select id, event_id, author_id, rtime from me_event_photo where id=%s", id)
        if r:
            return cls(*r[0])

    @classmethod
    def gets(cls, start=0, limit=20):
        r = store.execute("select count(1) from me_event_photo")
        total = r and r[0][0]
        rs = store.execute("select id from me_event_photo order by id desc limit %s,%s", (start, limit))
        return total, [cls.get(str(r[0])) for r in rs]

    @classmethod
    def new(cls, event_id, author_id, filename):
        #print 'upload', event_id, author_id, filename
        data = open(filename).read()
        if len(data) > MAX_SIZE:
            return "too_large"
        store.execute("insert into me_event_photo(event_id,author_id) values(%s,%s)", (event_id, author_id))
        store.commit()
        pid = store.get_cursor(table="me_event_photo").lastrowid
        cls.update_photo(pid, event_id, data)
        #print 'new photo', pid
        return pid

    @classmethod
    def update_photo(cls, pid, event_id, data):
        doubanfs.set("/me/evp-%s-%s-%s" % (event_id, pid, Cate.ORIGIN), data)
        o = scale(data, Cate.LARGE, DEFAULT_CONFIG)
        doubanfs.set("/me/evp-%s-%s-%s" % (event_id, pid, Cate.LARGE), o)
        for c in CATES:
            d = scale(o, c, DEFAULT_CONFIG)
            doubanfs.set("/me/evp-%s-%s-%s" % (event_id, pid, c), d)

    def rotate(self, direction):
        if direction in ['left', 'right']:
            data = self.photo_data(Cate.ORIGIN)
            with Image(blob=data) as img:
                img.rotate(direction == "left" and 270 or 90)
                data = img.make_blob()
                EventPhoto.update_photo(self.id, self.event_id, data)
                store.execute("update me_event_photo set rtime=%s where id=%s", (datetime.now(), self.id))
                store.commit()

    @property
    def path(self):
        return "/event/photo/%s/" % (self.id)

    @property
    def photo_url(self):
        return "%s/event/photo/%s/" % (SITE, self.id)

    @property
    def tags(self):
        return PhotoTag.gets_by_photo(self.id)

    @property
    def sort_time(self):
        return self.rtime

    def url(self, cate=Cate.LARGE):
        timestr = '$%0d' % time.mktime(self.rtime.timetuple())
        return "/p/evp%s-%s-%s%s.jpg" % (self.event_id, self.id, cate, timestr)

    def dynamic_url(self, x, y, scale='center-crop'):
        timestr = '$%0d' % time.mktime(self.rtime.timetuple())
        s = 'fs'
        if scale == 'center-crop':
            s = 'cc'
        return "/p/evp%s-%s-r_%s_%sx%s%s.jpg" % (self.event_id, self.id, s, x, y, timestr)

    def photo_data(self, cate):
        return doubanfs.get("/me/evp-%s-%s-%s" % (self.event_id, self.id, cate))

    @property
    def event(self):
        return Event.get(self.event_id)

    @property
    def author(self):
        return User(id=self.author_id)

    @property
    def author_card(self):
        return Card.get(self.author_id)

    @property
    def comment_num(self):
        r = store.execute("select count(id) from me_photo_comment where photo_id=%s", self.id)
        if r and r[0]:
            return r[0][0]

    @property
    def comments(self):
        rs = store.execute("select id, photo_id, author_id, content, rtime"
                " from me_photo_comment where photo_id=%s order by rtime", self.id)
        return [PhotoComment(*r) for r in rs]

    def comment(self, author_id, content):
        store.execute("insert into me_photo_comment(`photo_id`,`author_id`,`content`)"
            " values(%s,%s,%s)", (self.id, author_id, content));
        store.commit()
        cid = store.get_cursor(table="me_photo_comment").lastrowid
        Notify.new(self.author.id, author_id, Notify.TYPE_PHOTO_COMMENT, extra={"comment_id":cid, "photo_id":self.id})
        if '@' in content:
            from webapp.models.utils import mention_text
            ret = mention_text(content)
            for b, e, card_id, kind in ret['postions']:
                Notify.new(card_id, author_id, Notify.TYPE_PHOTO_COMMENT_MENTION,
                    extra={"card_id":self.author_id, "comment_id":cid, "photo_id":self.id})

    def uncomment(self, author_id, comment_id):
        PhotoComment.remove(author_id, comment_id)

    @property
    def like_num(self):
        r = store.execute("select count(liker_id) from me_photo_like where photo_id=%s", self.id)
        if r and r[0]:
            return r[0][0]

    def is_liked(self, user_id):
        r = store.execute("select 1 from me_photo_like where photo_id=%s and liker_id=%s", (self.id, user_id))
        if r and r[0]:
            return True
        return False

    @property
    def likers(self):
        rs = store.execute("select liker_id from me_photo_like where photo_id=%s", self.id)
        cids = []
        if rs:
            cids = [str(r[0]) for r in rs]
        return [User(id=i) for i in cids]

    def like(self, liker_id):
        store.execute("replace into me_photo_like(photo_id, liker_id) values(%s,%s)", (self.id, liker_id))
        store.commit()
        Notify.new(self.author.id, liker_id, Notify.TYPE_PHOTO_LIKE, extra={"photo_id":self.id})

    def can_remove(self, user_id):
        return user_id == self.author_id or self.event.can_edit(user_id)

    def can_edit(self, user_id):
        return user_id == self.author_id or self.event.can_edit(user_id)

    def remove(self):
        store.execute("delete from me_event_photo where id=%s", self.id)
        store.execute("delete from me_photo_like where photo_id=%s", self.id)
        store.execute("delete from me_photo_comment where photo_id=%s", self.id)
        store.commit()

class PhotoComment(object):

    def __init__(self, id, photo_id, author_id, content, rtime):
        self.id = str(id)
        self.photo_id = str(photo_id)
        self.author_id = str(author_id)
        self.content = content
        self.rtime = rtime

    @property
    def photo(self):
        return EventPhoto.get(self.photo_id)

    @property
    def author(self):
        return User(id=self.author_id)

    @property
    def author_card(self):
        return Card.get(self.author_id)

    @property
    def html(self):
        from webapp.models.utils import mention_text
        ret = mention_text(self.content)
        return ret['html']

    @classmethod
    def remove(cls, author_id, comment_id):
        store.execute("delete from me_photo_comment where"
            " `author_id`=%s and `id`=%s", (author_id, comment_id))
        store.commit()
