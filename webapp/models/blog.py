# models.blog
# -*- coding: UTF-8 -*-

from quixote.html import html_quote
from operator import itemgetter, attrgetter
from wand.image import Image
from config import DEVELOP_MODE
from datetime import datetime, timedelta
from libs import doubandb, doubanfs, Employee, cache, doubanmc, store, User, send_fireworks, publish_channel_msg
from webapp.models.consts import *
from webapp.models.notify import Notify
from webapp.models.utils import scale
from config import SITE
import simplejson as json
import re

class BlogComment(object):
    def __init__(self, id, blog_id, author_id, content, photo_id, rtime):
        self.id = str(id)
        self.blog_id = str(blog_id)
        self.author_id = str(author_id)
        self.content = content
        self.photo_id = photo_id
        self.rtime = rtime

    @property
    def html(self):
        from webapp.models.utils import mention_text
        ret = mention_text(self.content)
        return ret['html']

    @property
    def author(self):
        return User(id=self.author_id)

    @property
    def author_card(self):
        from webapp.models.card import Card
        return Card.get(self.author_id)

    @classmethod
    def remove(cls, author_id, comment_id):
        store.execute("delete from me_blog_comment where"
            " `author_id`=%s and `id`=%s", (author_id, comment_id))
        store.commit()

    def photo_data(self, cate):
        if self.photo_id > 0:
            return doubanfs.get("/me/bcp%s-%s-%s" % (self.id, self.photo_id, cate))

    def dynamic_photo(self, x, y, scale='center-crop'):
        if self.photo_id > 0:
            s = 'fs'
            if scale == 'center-crop':
                s = 'cc'
            return "/p/bc%s-%s-r_%s_%sx%s.jpg" % (self.id, self.photo_id, s, x, y)
        return ''

    @property
    def photo(self):
        if self.photo_id > 0:
            return "/p/bc%s-%s-%s.jpg" % (self.id, self.photo_id, Cate.LARGE)
        return ''

    @classmethod
    def get(cls, id):
        r = store.execute("select id, blog_id, author_id, content, photo_id, rtime"
                " from me_blog_comment where id=%s", id)
        if r and r[0]:
            return cls(*r[0])

class Topic(object):

    @classmethod
    def get(cls, id):
        r = store.execute("select id, name, rtime from me_topic where id=%s", id)
        if r and r[0]:
            return cls(*r[0])

    @classmethod
    def get_by_name(cls, name):
        name = name.lower()
        r = store.execute("select id, name, rtime from me_topic where name=%s", name)
        if r and r[0]:
            return cls(*r[0])

    @classmethod
    def bind(cls, name, user_id, blog_id):
        if '#' in name:
            return
        name = name.lower()
        r = store.execute("select id from me_topic where name=%s", name)
        topic_id = None
        if r and r[0]:
            topic_id = r[0][0]
        else:
            store.execute("insert into me_topic(name) values(%s)", name)
            topic_id = store.get_cursor(table="me_topic").lastrowid
        if topic_id:
            store.execute("replace into me_topic_blog(user_id, topic_id, blog_id)"
                    " values(%s,%s,%s)", (user_id, topic_id, blog_id))
            store.commit()
        return topic_id

    def __init__(self, id, name, rtime):
        self.id = str(id)
        self.name = name.upper()
        self.rtime = rtime

    @property
    def path(self):
        return '/topic/%s' % html_quote(self.name)

    @property
    def url(self):
        return '%s/topic/%s' % (SITE, html_quote(self.name))

    @property
    def blogs(self):
        rs = store.execute("select blog_id from me_topic_blog where topic_id=%s order by blog_id desc", self.id)
        return [Blog.get(str(r[0])) for r in rs]

    @classmethod
    def gets(cls, start=0, limit=20):
        r = store.execute("select count(1) from me_topic")
        total = r and r[0][0]
        rs = store.execute("select id from me_topic order by id desc limit %s,%s", (start, limit))
        return total, [cls.get(str(r[0])) for r in rs]

    @classmethod
    def gets_by_blog(cls, blog_id):
        rs = store.execute("select topic_id from me_topic_blog where blog_id=%s", blog_id)
        return [cls.get(str(r[0])) for r in rs]

class Blog(object):

    FLAG_NORMAL = 'N'
    FLAG_DELETED = 'D'

    TYPE_NOTIFY = 'N'
    TYPE_BLOG = 'B'
    TYPE_THREAD = 'T'

    BLOG_TEXT = 'BT'
    BLOG_PHOTO = 'BP'
    BLOG_AUDIO = 'BA'
    BLOG_ICON = 'BI'
    BLOG_EVENT = 'BE'

    ICON_DICT = {
        BLOG_TEXT:'icon-leaf',
        BLOG_PHOTO:'icon-camera',
        BLOG_ICON:'icon-user',
        BLOG_EVENT:'icon-glass',
        BLOG_AUDIO:'icon-music',
    }

    def __init__(self, id, user_id, flag, btype, action, content, extra, photo_id, audio_id, n_like, n_unlike, n_comment, ctime):
        self.id = str(id)
        self.user_id = str(user_id)
        self.flag = flag
        self.btype = btype
        self.action = action
        self.content = content
        self.photo_id = photo_id
        self.audio_id = audio_id
        self.n_like = n_like
        self.n_unlike = n_unlike
        self.n_comment = n_comment
        self.ctime = ctime
        try:
            self.extra = json.loads(extra)
        except:
            self.extra = {}
        if self.action in [self.BLOG_ICON, self.BLOG_EVENT]:
            self.photo_id = self.extra.get('photo_id', 0)

    ## content/action/author_id/author_name/author_icon/create/image
    def fireworks_dict(self):
        d = self.json_dict(None)
        ret = {
            'id': 'me-blog-%s' % self.id,
            'author_id': self.user_id,
            'author_name': self.card.screen_name,
            'author_icon': self.card.icon,
            'text': d['content'],
            'image': self.photo,
            'created': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
        }
        if self.action == self.BLOG_ICON:
            ret['image'] = '';
            ret['text'] = '上传了新真相  ╮(╯▽╰)╭';
        return ret

    def json_dict(self, user):
        ret = {
            'id': self.id,
            'alt': self.url,
            'type': self.btype,
            'action': self.action,
            'like_num': self.n_like,
            'unlike_num': self.n_unlike,
            'comment_num': self.n_comment,
            'created': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
            'author': self.card.json_dict(user),
            'photo':self.photo,
            'extra':self.extra,
        }
        if self.btype == self.TYPE_BLOG:
            ret['content'] = self.content
            ret['html'] = self.html
        elif self.btype == self.TYPE_NOTIFY:
            from libs.template import stf
            html = str(stf("/blog/utils.html", "notify_inline", n=self))
            html = html.replace('\n', '').replace('\t', '')
            H5_RE = re.compile(r'<h5>(.+)</h5>')
            HREF_RE = re.compile(r'<a [^>]+>|</a>')
            r = H5_RE.findall(html)
            html = r and r[0] or ''
            ret['html'] = html
            ret['content'] = HREF_RE.sub('', html)
        return ret

    @property
    def html(self):
        from webapp.models.utils import mention_text
        ret = mention_text(self.content, True)
        return ret['html']

    @property
    def sort_time(self):
        return self.ctime

    @property
    def card(self):
        from webapp.models.card import Card
        return Card.get(self.user_id)

    @property
    def event(self):
        from webapp.models.event import Event
        eid = self.extra.get('event_id', None)
        if eid:
            return Event.get(eid)

    @property
    def owner(self):
        return User(self.user_id)

    @property
    def author(self):
        uid = self.extra.get('author_id', None)
        if uid:
            try:
                return User(uid)
            except:
                pass

    @property
    def author_card(self):
        from webapp.models.card import Card
        uid = self.extra.get('author_id', None)
        if uid:
            return Card.get(uid)

    @property
    def icon(self):
        if self.btype == self.TYPE_NOTIFY:
            return Notify.ICON_DICT.get(self.action, '')
        return self.ICON_DICT.get(self.action, '')

    @property
    def type_name(self):
        if self.btype == self.TYPE_THREAD:
            return '帖子'
        return '广播'

    @classmethod
    def get(cls, id):
        r = store.execute("select `id`, `user_id`, `flag`, `btype`, `action`, "
                " `content`, `extra`, `photo_id`, `audio_id`, `n_like`, `n_unlike`,"
                "`n_comment`, `ctime` from me_blog where id=%s and flag=%s", (id, cls.FLAG_NORMAL))
        if r and r[0]:
            return cls(*r[0])

    @classmethod
    def remove(cls, id, user_id):
        store.execute("update me_blog set flag=%s where `id`=%s and user_id=%s", (cls.FLAG_DELETED, id, user_id))
        store.execute("delete from me_topic_blog where blog_id=%s", id)
        store.commit()

    @classmethod
    def get_photo_blogs(cls, card_id=0, start=0, limit=20):
        if card_id:
            r = store.execute("select count(1) from me_blog where user_id=%s"
                " and flag=%s and action=%s", (card_id, cls.FLAG_NORMAL, cls.BLOG_PHOTO))
            total = r[0][0]
            rs = store.execute("select `id`, `user_id`, `flag`, `btype`, `action`, `content`, `extra`,"
                "`photo_id`, `audio_id`, `n_like`, `n_unlike`, `n_comment`, `ctime` from me_blog"
                " where user_id=%s and flag=%s and action=%s order by id desc limit %s,%s",
                (card_id, cls.FLAG_NORMAL, cls.BLOG_PHOTO, start, limit))
        else:
            r = store.execute("select count(1) from me_blog"
                    " where flag=%s and action=%s", (cls.FLAG_NORMAL, cls.BLOG_PHOTO))
            total = r[0][0]
            rs = store.execute("select `id`, `user_id`, `flag`, `btype`, `action`, `content`, `extra`,"
                    "`photo_id`, `audio_id`, `n_like`, `n_unlike`, `n_comment`, `ctime` from me_blog"
                    " where flag=%s and action=%s order by id desc limit %s,%s",
                    (cls.FLAG_NORMAL, cls.BLOG_PHOTO, start, limit))
        return total, [cls(*r) for r in rs]

    @classmethod
    def gets(cls, card_id=0, start=0, limit=20, blog_type=''):
        total = 0
        TYPE_DICT = {
            'a':'',
            'b':cls.TYPE_BLOG,
            'n':cls.TYPE_NOTIFY,
        }
        blog_type = TYPE_DICT.get(blog_type, '')
        if card_id:
            if blog_type:
                r = store.execute("select count(1) from me_blog where user_id=%s"
                    " and flag=%s and btype=%s", (card_id, cls.FLAG_NORMAL, blog_type))
            else:
                r = store.execute("select count(1) from me_blog where user_id=%s and flag=%s and btype!=%s", (card_id, cls.FLAG_NORMAL, cls.TYPE_THREAD))
            total = r[0][0]
            if blog_type:
                rs = store.execute("select `id`, `user_id`, `flag`, `btype`, `action`, `content`, `extra`,"
                    "`photo_id`, `audio_id`, `n_like`, `n_unlike`, `n_comment`, `ctime` from me_blog"
                    " where user_id=%s and flag=%s and btype=%s order by id desc limit %s,%s",
                    (card_id, cls.FLAG_NORMAL, blog_type, start, limit))
            else:
                rs = store.execute("select `id`, `user_id`, `flag`, `btype`, `action`, `content`, `extra`,"
                    "`photo_id`, `audio_id`, `n_like`,`n_unlike`, `n_comment`, `ctime` from me_blog"
                    " where user_id=%s and flag=%s and btype!=%s order by id desc limit %s,%s", (card_id,
                        cls.FLAG_NORMAL, cls.TYPE_THREAD, start, limit))
        else:
            if blog_type:
                r = store.execute("select count(1) from me_blog where flag=%s"
                    " and btype=%s", (cls.FLAG_NORMAL, blog_type))
            else:
                r = store.execute("select count(1) from me_blog where flag=%s and btype!=%s", (cls.FLAG_NORMAL,
                    cls.TYPE_THREAD))
            total = r[0][0]
            if blog_type:
                rs = store.execute("select `id`, `user_id`, `flag`, `btype`, `action`, `content`, `extra`,"
                    "`photo_id`, `audio_id`, `n_like`, `n_unlike`, `n_comment`, `ctime` from me_blog"
                    " where flag=%s and btype=%s order by id desc limit %s,%s", (cls.FLAG_NORMAL, blog_type, start, limit))
            else:
                rs = store.execute("select `id`, `user_id`, `flag`, `btype`, `action`, `content`, `extra`,"
                    "`photo_id`, `audio_id`, `n_like`, `n_unlike`, `n_comment`, `ctime` from me_blog"
                    " where flag=%s and btype!=%s order by id desc limit %s,%s", (cls.FLAG_NORMAL,
                        cls.TYPE_THREAD, start, limit))
        return total, [cls(*r) for r in rs]

    @classmethod
    def new(cls, user_id, btype, action='', content='', filename='', ftype='', extra={}, ctime=None):
        #print 'Blog new', user_id, btype, action, content, filename, ftype, extra, ctime
        try:
            extra = json.dumps(extra)
        except:
            extra = "{}"
        now = ctime or datetime.now()
        store.execute("insert into me_blog(`user_id`,`btype`,`action`, `content`, `extra`, `ctime`)"
                " values(%s,%s,%s,%s,%s,%s)", (user_id, btype, action or cls.BLOG_TEXT, content, extra, now))
        id = store.get_cursor(table="me_blog").lastrowid
        if filename and ftype:
            ftype = CONTENT_TYPE_DICT.get(ftype, None)
            if not ftype:
                return "invalid_type"
            data = open(filename).read()
            if len(data) > MAX_SIZE:
                return "too_large"
            if ftype in ['jpg', 'png', 'gif']:
                store.execute("insert into me_blog_photo(blog_id,author_id,ftype) values(%s,%s,%s)", (id, user_id, ftype))
                photo_id = store.get_cursor(table="me_blog_photo").lastrowid
                store.execute("update me_blog set photo_id=%s,action=%s where id=%s", (photo_id, cls.BLOG_PHOTO, id))
                doubanfs.set("/me/bp%s-%s-%s" % (id, photo_id, Cate.ORIGIN), data)
                o = scale(data, Cate.LARGE, DEFAULT_CONFIG)
                doubanfs.set("/me/bp%s-%s-%s" % (id, photo_id, Cate.LARGE), o)
            elif ftype in ['mp3']:
                store.execute("insert into me_blog_audio(blog_id,author_id,ftype) values(%s,%s,%s)", (id, user_id, ftype))
                audio_id = store.get_cursor(table="me_blog_audio").lastrowid
                store.execute("update me_blog set audio_id=%s,action=%s where id=%s", (audio_id, cls.BLOG_AUDIO, id))
                doubanfs.set("/me/ba%s-%s-%s" % (id, audio_id, Cate.ORIGIN), data)

        store.commit()
        if '@' in content or '#' in content:
            from webapp.models.utils import mention_text
            ret = mention_text(content, True)
            for b, e, rid, kind in ret['postions']:
                if kind == 'card':
                    card_id = rid
                    Notify.new(card_id, user_id, Notify.TYPE_BLOG_MENTION,
                        extra={"card_id":user_id, "blog_id":id})
                elif kind == 'topic':
                    name = rid
                    topic_id = Topic.bind(name, user_id, id)
        if btype in [cls.TYPE_BLOG, cls.TYPE_NOTIFY]:
            blog = Blog.get(id)
            send_fireworks(blog.fireworks_dict())
        return id

    def photo_data(self, cate):
        if self.photo_id > 0:
            return doubanfs.get("/me/bp%s-%s-%s" % (self.id, self.photo_id, cate))

    @property
    @cache("me:bp-size:{self.id}", expire=3600*24)
    def photo_size(self):
        d = self.photo_data(Cate.LARGE)
        if d:
            try:
                with Image(blob=d) as img:
                    return img.width, img.height
            except:
                pass
        return 0, 0

    def audio_data(self, cate=Cate.ORIGIN):
        if self.audio_id > 0:
            return doubanfs.get("/me/ba%s-%s-%s" % (self.id, self.audio_id, cate))

    def comment(self, author_id, content, filename='', ftype=''):
        print 'comment', filename, ftype
        store.execute("insert into me_blog_comment(`blog_id`,`author_id`,`content`)"
            " values(%s,%s,%s)", (self.id, author_id, content));
        cid = store.get_cursor(table="me_blog_comment").lastrowid
        store.execute("update me_blog set `n_comment`=`n_comment`+1 where id=%s", self.id)
        store.commit()
        print 'comment_id', cid

        if cid and filename and ftype:
            ftype = CONTENT_TYPE_DICT.get(ftype, None)
            if ftype in ['jpg', 'png', 'gif']:
                data = open(filename).read()
                store.execute("update me_blog_comment set photo_id=photo_id+1,"
                    "rtime=rtime where id=%s", cid)
                store.commit()
                doubanfs.set("/me/bcp%s-%s-%s" % (cid, 1, Cate.ORIGIN), data)
                o = scale(data, Cate.LARGE, DEFAULT_CONFIG)
                doubanfs.set("/me/bcp%s-%s-%s" % (cid, 1, Cate.LARGE), o)

        Notify.new(self.user_id, author_id, Notify.TYPE_BLOG_COMMENT, extra={"comment_id":cid, "blog_id":self.id})
        if '@' in content or '#' in content:
            from webapp.models.utils import mention_text
            ret = mention_text(content, True)
            for b, e, card_id, kind in ret['postions']:
                if kind == 'card':
                    Notify.new(card_id, author_id, Notify.TYPE_BLOG_COMMENT_MENTION,
                        extra={"card_id":self.user_id, "comment_id":cid, "blog_id":self.id})
        aids = [cm.author_id for cm in self.comments if cm.author_id not in [self.user_id, author_id]]
        for aid in set(aids):
            Notify.new(aid, author_id, Notify.TYPE_BLOG_REPLY, extra={"comment_id":cid, "blog_id":self.id})

    def uncomment(self, author_id, comment_id):
        BlogComment.remove(author_id, comment_id)

    @property
    def topics(self):
        return Topic.gets_by_blog(self.id)

    @property
    def comments(self):
        rs = store.execute("select id, blog_id, author_id, content, photo_id, rtime"
                " from me_blog_comment where blog_id=%s order by rtime", self.id)
        return [BlogComment(*r) for r in rs]

    @property
    def path(self):
        return '/blog/%s/' % self.id

    @property
    def url(self):
        return '%s/blog/%s/' % (SITE, self.id)

    def is_liked(self, liker_id):
        r = store.execute("select 1 from me_blog_like where blog_id=%s and liker_id=%s", (self.id, liker_id))
        if r and r[0][0]:
            return True
        return False

    def like(self, liker_id):
        if not self.is_liked(liker_id):
            store.execute("replace into me_blog_like(blog_id, liker_id) values(%s,%s)", (self.id, liker_id))
            store.execute("update me_blog set `n_like`=`n_like`+1 where id=%s", self.id)
            store.commit()
            Notify.new(self.user_id, liker_id, Notify.TYPE_BLOG_LIKE, extra={'blog_id':self.id})

    def is_unliked(self, unliker_id):
        r = store.execute("select 1 from me_blog_unlike where blog_id=%s and unliker_id=%s", (self.id, unliker_id))
        if r and r[0][0]:
            return True
        return False

    def unlike(self, unliker_id):
        if not self.is_unliked(unliker_id):
            store.execute("replace into me_blog_unlike(blog_id, unliker_id) values(%s,%s)", (self.id, unliker_id))
            store.execute("update me_blog set `n_unlike`=`n_unlike`+1 where id=%s", self.id)
            store.commit()
            Notify.new(self.user_id, unliker_id, Notify.TYPE_BLOG_UNLIKE, extra={'blog_id':self.id})

    @property
    def likers(self):
        rs = store.execute("select liker_id from me_blog_like where blog_id=%s", self.id)
        cids = []
        if rs:
            cids = [str(r[0]) for r in rs]
        return [User(id=i) for i in cids]

    @classmethod
    def photo_ftype(cls, id):
        r = store.execute("select ftype from me_blog_photo where id=%s", id)
        if r and r[0]:
            return r[0][0]
        return 'jpg'

    @property
    def photo(self):
        if self.photo_id > 0:
            if self.action == self.BLOG_ICON:
                return self.card.photo_url(self.photo_id)
            elif self.action == self.BLOG_EVENT:
                return self.event and self.event.cover()
            return "/p/b%s-%s-%s.%s" % (self.id, self.photo_id, Cate.LARGE, self.photo_ftype(self.photo_id))
        return ''

    @property
    def origin_photo(self):
        if self.photo_id > 0:
            if self.action == self.BLOG_ICON:
                return self.card.origin_photo(self.photo_id)
            elif self.action == self.BLOG_EVENT:
                return self.event and self.event.cover(Cate.ORIGIN)
            return "/p/b%s-%s-%s.%s" % (self.id, self.photo_id, Cate.ORIGIN, self.photo_ftype(self.photo_id))
        return ''

    def dynamic_photo(self, x, y, scale='center-crop'):
        if self.photo_id > 0:
            if self.action == self.BLOG_ICON:
                return self.card.dynamic_photo(x, y, scale, photo_id=self.photo_id)
            elif self.action == self.BLOG_EVENT:
                return self.event and self.event.dynamic_cover(x, y, scale)
            s = 'fs'
            if scale == 'center-crop':
                s = 'cc'
            return "/p/b%s-%s-r_%s_%sx%s.%s" % (self.id, self.photo_id, s, x, y, self.photo_ftype(self.photo_id))
        return ''

    @classmethod
    def audio_ftype(cls, id):
        r = store.execute("select ftype from me_blog_audio where id=%s", id)
        if r and r[0]:
            return r[0][0]
        return 'mp3'

    @property
    def audio(self):
        if self.audio_id > 0:
            return "/a/b%s-%s-%s.%s" % (self.id, self.audio_id, Cate.ORIGIN, self.audio_ftype(self.audio_id))
        return ''

    @property
    def origin_audio(self):
        return self.audio


class Rec(object):

    from webapp.models.group import Group, Thread
    RTYPE_DICT = {
        'group': Group,
        'thread': Thread,
    }

    NAME_DICT = {
        'group': '群组',
        'thread': '帖子',
    }

    def __init__(self, blog, rtype, obj_id):
        self.blog = blog
        self.rtype = rtype
        self.obj_id = obj_id

    @classmethod
    def get(cls, id):
        b = Blog.get(id)
        if b and b.btype == Blog.TYPE_NOTIFY and b.action == Notify.TYPE_REC:
            return cls(b, b.extra.get('type', ''), b.extra.get('id', ''))

    @property
    def type_name(self):
        return self.NAME_DICT.get(self.rtype, '')

    @property
    def name(self):
        return self.obj.rec_name

    @classmethod
    def new(cls, user_id, rtype, rec_id):
        rec_cls = cls.RTYPE_DICT.get(rtype, None)
        if rec_cls:
            obj = rec_cls.get(rec_id)
            if obj:
                return Notify.new(user_id, user_id, Notify.TYPE_REC, extra={'type':rtype, 'id':rec_id})

    @property
    def obj(self):
        rec_cls = self.RTYPE_DICT.get(self.rtype, None)
        return rec_cls.get(self.obj_id)
