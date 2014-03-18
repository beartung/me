# models.card
# -*- coding: UTF-8 -*-

from operator import itemgetter, attrgetter
from wand.image import Image
from config import DEVELOP_MODE
from datetime import datetime, timedelta
from libs import doubandb, doubanfs, Employee, cache, doubanmc, store, User
from webapp.models.consts import *
from webapp.models.notify import Notify
from webapp.models.profile import Profile
from webapp.models.badage import Badage
from webapp.models.question import Question, Answer
from config import SITE
import simplejson as json
import math

CHART_BLACK_LIST_UIDS = [
    '46555103', #Ruby = =
    ]

class Comment(object):

    def __init__(self, id, card_id, author_id, content, rtime):
        self.id = str(id)
        self.card_id = str(card_id)
        self.author_id = str(author_id)
        self.content = content
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
        return Card.get(self.author_id)

    @classmethod
    def remove(cls, author_id, comment_id):
        store.execute("delete from me_comment where"
            " `author_id`=%s and `id`=%s", (author_id, comment_id))
        store.commit()

class Card(object):
    FLAG_NORMAL = 'N'
    FLAG_HIDE = 'H'
    MC_KEY = 'me-card:%s'

    def __init__(self, id, uid, email, skype, name, alias, phone, photo_id, flag, join_time, rtime, ctime):
        self.id = str(id)
        self.uid = uid
        self.email = email
        self.skype = skype
        self.name  = name
        self.alias = alias
        self.phone = phone
        self.join_time = join_time or ''
        self.photo_id = photo_id
        self.flag  = flag
        self.rtime = rtime
        self.ctime = ctime

    @property
    def sort_date(self):
        return self.join_time

    @property
    def sort_time(self):
        return self.rtime

    @property
    def profile(self):
        return Profile.get(self.id)

    def set_profile2(self, profile):
        doubandb.set("me/card/profile2-%s" % self.id, profile)

    @property
    def profile2(self):
        return doubandb.get("me/card/profile2-%s" % self.id, {})

    @property
    def department(self):
        return self.profile2.get('department', '')

    @property
    def selfintro(self):
        return self.profile2.get('selfintro', '') or self.profile.intro

    @property
    def position(self):
        return self.profile2.get('position', '')

    @property
    def path(self):
        return "/card/%s/" % self.uid

    @property
    def url(self):
        return "%s/card/%s/" % (SITE, self.uid)

    @property
    def is_basic(self):
        return self.email and self.name

    @property
    def is_hide(self):
        return self.flag == self.FLAG_HIDE

    @property
    def is_full(self):
        return self.is_basic and self.skype and self.join_time and self.alias and self.photo > 0 and self.profile.sex and self.profile.love and self.profile.marriage and self.profile.birthday and self.profile.hometown

    def json_dict(self, user):
        ret = {}
        if not self.owner:
            return {}
        ret['id'] = self.id
        ret['alt'] = self.url
        ret['uid'] = self.uid
        ret['name'] = self.screen_name
        ret['icon'] = self.icon
        ret['email'] = self.email
        ret['skype'] = self.skype
        ret['alias'] = self.alias
        ret['join_time'] = self.join_time and self.join_time.strftime('%Y-%m-%d')
        if not DEVELOP_MODE:
            ret['city'] = self.owner.profile().get('city','城市')
        else:
            ret['city'] = 'city'
        ret['reg_time'] = self.owner.reg_time.strftime('%Y-%m-%d')
        ret['photo'] = SITE + self.photo
        ret['updated'] = self.rtime.strftime('%Y-%m-%d')
        ret['created'] = self.ctime.strftime('%Y-%m-%d')
        ret['like_num'] = self.like_num
        ret['comment_num'] = self.comment_num
        ret['url'] = self.url
        ret['province'] = self.profile.province
        ret['hometown'] = self.profile.hometown
        ret['resume'] = self.profile.resume
        ret['intro'] = self.profile.intro
        ret['weibo'] = self.profile.weibo
        ret['instagram'] = self.profile.instagram
        ret['blog'] = self.profile.blog
        ret['code'] = self.profile.code
        ret['github'] = self.profile.github
        ret['tags'] = self.tags
        ret['badages'] = [b.json_dict() for b in self.badages]
        ret['sex'] = self.profile.sex
        ret['love'] = self.profile.love
        ret['marriage'] = self.profile.marriage
        ret['zodiac'] = self.profile.zodiac
        ret['astro'] = self.profile.astro
        if user:
            ret['is_liked'] = self.is_liked(user.id)
            ret['user_tags'] = [t.json_dict(user) for t in self.ptags]
        return ret

    def can_view(self, user, attr=None):
        if user:
            if user.id == self.id:
                return True
            if self.flag == self.FLAG_HIDE:
                return False
            card = Card.get(user.id)
            if not attr:
                return card and card.is_full
            else:
                v = getattr(card.profile, attr)
                return v
        return False

    @classmethod
    def search(cls, q):
        cids = []
        rs = store.execute("select user_id from me_card where name like %s and flag=%s", (q + '%%', cls.FLAG_NORMAL))
        if rs:
            cids = [str(r[0]) for r in rs]
        else:
            rs = store.execute("select user_id from me_card where uid like %s and flag=%s", (q + '%%', cls.FLAG_NORMAL))
            if rs:
                cids = [str(r[0]) for r in rs]
            else:
                rs = store.execute("select user_id from me_card where alias like %s and flag=%s", (q + '%%', cls.FLAG_NORMAL))
                if rs:
                    cids = [str(r[0]) for r in rs]
                else:
                    rs = store.execute("select user_id from me_card where email like %s and flag=%s", (q + '%%', cls.FLAG_NORMAL))
                    if rs:
                        cids = [str(r[0]) for r in rs]
                    else:
                        rs = store.execute("select user_id from me_card where skype like %s"
                                           " and flag=%s", (q + '%%', cls.FLAG_NORMAL))
                        if rs:
                            cids = [str(r[0]) for r in rs]
        return [cls.get(i) for i in cids]

    @property
    def owner(self):
        return User(id=self.id)

    @property
    def icon(self):
        return self.owner and self.owner.picture(default=True) or 'http://img3.douban.com/icon/user_normal.jpg'

    @property
    def screen_name(self):
        return self.owner and self.owner.name

    @classmethod
    def hide(cls, card_id, admin_id):
        if admin_id in ADMINS:
            store.execute("update me_card set flag=%s where user_id=%s", (cls.FLAG_HIDE, card_id))
            store.commit()
            card = cls.get(card_id)
            if card:
                doubanmc.delete(cls.MC_KEY % card.id)
                doubanmc.delete(cls.MC_KEY % card.uid)

    @classmethod
    def new(cls, user_id, uid):
        now = datetime.now()
        store.execute("insert into me_card(`user_id`,`uid`, `ctime`) values(%s,%s,%s)"
                " on duplicate key update rtime=%s", (user_id, uid, now, now))
        store.commit()
        doubanmc.delete("me:users:dict")

    @classmethod
    def get_by_ldap(cls, email):
        if not email.endswith('@douban.com'):
            email = email + '@douban.com'
        r = store.execute("select `user_id` from me_card where email=%s and flag=%s", (email, cls.FLAG_NORMAL))
        if r and r[0]:
            return cls.get(r[0])

    @classmethod
    @cache("me-card:{id}", expire=3600)
    def get(cls, id):
        r = store.execute("select `user_id`, `uid`, `email`, `skype`, `name`, `alias`, `phone`, `photo`,"
                " `flag`, `join_time`, `rtime`, `ctime`"
                " from me_card where `user_id`=%s", id)
        card = None
        if r and r[0]:
            card = cls(*r[0])
        else:
            r = store.execute("select `user_id`, `uid`, `email`, `skype`, `name`, `alias`, `phone`, `photo`,"
                    " `flag`, `join_time`, `rtime`, `ctime`"
                    " from me_card where `uid`=%s", id)
            if r and r[0]:
                card = cls(*r[0])
        if card:
            try:
                employee = Employee.dget(card.id)
                if employee:
                    #print 'get info by dae service', employee.fullname, employee.douban_mail, employee.entry_date
                    if employee.fullname:
                        card.name = employee.fullname
                    if employee.douban_mail:
                        card.email = employee.douban_mail
                    if employee.entry_date:
                        card.join_time = datetime.strptime(employee.entry_date, '%Y-%m-%d')
            except:
                print "dae service EmployeeClient error user_id %s" % (card and card.id or '0')
            print 'card', id, card.id, card.uid, card.email, card.name
        return card

    def update_account(self, name, email):
        store.execute("update me_card set email=%s, `name`=%s where `user_id`=%s", (email, name, self.id))
        store.commit()
        doubanmc.delete(self.MC_KEY % self.id)
        doubanmc.delete(self.MC_KEY % self.uid)

    def update_basic(self, name, skype, alias, join_time):
        store.execute("update me_card set `name`=%s, skype=%s, `alias`=%s, join_time=%s where"
            " `user_id`=%s", (name, skype, alias, join_time, self.id))
        store.commit()
        doubanmc.delete(self.MC_KEY % self.id)
        doubanmc.delete(self.MC_KEY % self.uid)

    def update_profile(self, sex, love, zodiac, astro, birthday, marriage, province, hometown,
            weibo, instagram, blog, code, github, resume, intro):
        Profile.update(self.id, sex, love, zodiac, astro, birthday, marriage, province, hometown,
            weibo, instagram, blog, code, github, resume, intro)

    def update_photo(self, filename):
        data = open(filename).read()
        #print 'update photo old_id', old_id
        if len(data) > MAX_SIZE:
            return "too_large"
        return self.update_photo_data(data)

    def update_photo_id(self, photo_id):
        store.execute("update me_card set `photo`=%s where `user_id`=%s", (photo_id, self.id))
        store.commit()
        doubanmc.delete(self.MC_KEY % self.id)
        doubanmc.delete(self.MC_KEY % self.uid)

    def update_photo_data(self, data):
        success = False
        old_id = self.photo_id
        try:
            new_id = old_id + 1
            doubanfs.set("/me/card/%s/photo/%s/%s" % (self.id, new_id, Cate.ORIGIN), data)
            from webapp.models.utils import scale
            d = scale(data, Cate.LARGE, DEFAULT_CONFIG)
            doubanfs.set("/me/card/%s/photo/%s/%s" % (self.id, new_id, Cate.LARGE), d)
            print "update photo success photo_id=%s" % new_id
            store.execute("update me_card set `photo`=%s where `user_id`=%s", (new_id, self.id))
            store.commit()
            success = True
        except:
            print "doubanfs write fail!!! %s" % self.id
            self.photo_id = old_id
            store.execute("update me_card set `photo`=`photo`-1 where `user_id`=%s", self.id)
            store.commit()
            doubanfs.delete("/me/card/%s/photo/%s/%s" % (self.id, new_id, Cate.LARGE))
            doubanfs.delete("/me/card/%s/photo/%s/%s" % (self.id, new_id, Cate.ORIGIN))
            print 'rollback photo to old_id', old_id

        if success:
            Notify.new(self.id, self.id, Notify.TYPE_CHANGE_PHOTO, extra={'photo_id':new_id})
            print "send change photo blog"
            from webapp.models.blog import Blog
            Blog.new(self.id, Blog.TYPE_BLOG, Blog.BLOG_ICON, extra={'photo_id':new_id})


        doubanmc.delete(self.MC_KEY % self.id)
        doubanmc.delete(self.MC_KEY % self.uid)

    def recreate_photo(self):
        try:
            data = doubanfs.get("/me/card/%s/photo/%s/%s" % (self.id, self.photo_id, Cate.ORIGIN))
            d = scale(data, Cate.LARGE, DEFAULT_CONFIG)
            doubanfs.set("/me/card/%s/photo/%s/%s" % (self.id, self.photo_id, Cate.LARGE), d)
        except:
            print "doubanfs write fail!!! %s" % self.id

    @property
    def photo(self):
        if self.photo_id > 0:
            return "/p/%s-%s-%s.jpg" % (self.id, self.photo_id, Cate.LARGE)
        return ''

    def origin_photo(self, photo_id):
        if photo_id <= self.photo_id:
            return "/p/%s-%s-%s.jpg" % (self.id, photo_id, Cate.ORIGIN)
        return ''

    def photo_url(self, photo_id):
        if photo_id <= self.photo_id:
            return "/p/%s-%s-%s.jpg" % (self.id, photo_id, Cate.LARGE)
        return ''

    def dynamic_photo(self, x, y, scale='center-crop', photo_id=0):
        if photo_id < 1:
            photo_id = self.photo_id
        if photo_id > 0:
            s = 'fs'
            if scale == 'center-crop':
                s = 'cc'
            return "/p/%s-%s-r_%s_%sx%s.jpg" % (self.id, photo_id, s, x, y)
        return ''

    @property
    def photo_urls(self):
        return ["/p/%s-%s-%s.jpg" % (self.id, i, Cate.LARGE) for i in xrange(0, self.photo_id)]

    @property
    def like_num(self):
        r = store.execute("select count(1) from me_like where user_id=%s", self.id)
        if r and r[0]:
            return r[0][0]

    def likers(self):
        rs = store.execute("select liker_id from me_like where user_id=%s", self.id)
        cids = []
        if rs:
            cids = [str(r[0]) for r in rs]
        return [User(id=i) for i in cids]

    def is_liked(self, liker_id):
        r = store.execute("select 1 from me_like where user_id=%s and liker_id=%s", (self.id, liker_id))
        if r and r[0][0]:
            return True
        return False

    @classmethod
    def gets(cls, cate='', start=0, limit=20):
        cids = []
        if cate == 'photo':
            r = store.execute("select count(1) user_id from me_card where photo>0 and flag=%s", cls.FLAG_NORMAL)
            n = r and r[0][0]
            rs = store.execute("select user_id from me_card where photo>0 and flag=%s order by rtime desc"
                " limit %s, %s", (cls.FLAG_NORMAL, start, limit))
        else:
            r = store.execute("select count(1) user_id from me_card where flag=%s", cls.FLAG_NORMAL)
            n = r and r[0][0]
            rs = store.execute("select user_id from me_card where flag=%s order by rtime desc"
                " limit %s, %s", (cls.FLAG_NORMAL, start, limit))
        if rs:
            cids = [str(r[0]) for r in rs]
        return n, [cls.get(i) for i in cids]

    @classmethod
    def gets_by_time(cls, year='', start=0, limit=20):
        n, cids = cls.gets_ids_by_time(year)
        return n, [cls.get(i) for i in cids[start:start+limit]]

    @classmethod
    @cache("me-cards-by-time:{year}", expire=3600)
    def gets_ids_by_time(cls, year=''):
        cids = []
        if not year:
            r = store.execute("select count(1) from me_card where photo>0 and flag=%s", cls.FLAG_NORMAL)
            n = r and r[0][0]
            rs = store.execute("select user_id from me_card where flag=%s order by join_time desc", cls.FLAG_NORMAL)
        else:
            start = '%s-01-01 00:00:00' % year
            end = '%s-12-31 23:00:00' % year
            rs = store.execute("select user_id from me_card where photo>0 and flag=%s and"
                    " join_time > %s and join_time < %s order by join_time desc", (cls.FLAG_NORMAL, start, end))
            n = len(rs)
        if rs:
            cids = [str(r[0]) for r in rs]
        return n, cids

    @classmethod
    def gets_all(cls):
        rs = store.execute("select user_id from me_card where join_time > 0 and flag=%s order by join_time", cls.FLAG_NORMAL)
        cids = []
        if rs:
            cids = [str(r[0]) for r in rs]
        return [cls.get(i) for i in cids]

    @classmethod
    def gets_by_astro(cls, astro):
        astros = [r[1] for r in ASTROS]
        index = astros.index(astro)
        rs = store.execute("select user_id from me_profile where astro=%s", index)
        return [cls.get(r[0]) for r in rs]

    @classmethod
    def gets_by_zodiac(cls, zodiac):
        zodiacs = [r[1] for r in ZODIACS]
        index = zodiacs.index(zodiac)
        rs = store.execute("select user_id from me_profile where zodiac=%s", index)
        return [cls.get(r[0]) for r in rs]

    @classmethod
    def gets_by_province(cls, province):
        rs = store.execute("select user_id from me_profile where province=%s", province)
        return [cls.get(r[0]) for r in rs]

    @classmethod
    def gets_by_hometown(cls, city):
        rs = store.execute("select user_id from me_profile where hometown=%s", city)
        return [cls.get(r[0]) for r in rs]

    @classmethod
    def gets_by_tag(cls, tag):
        r = store.execute("select id from me_tag where name=%s", tag)
        if r and r[0]:
            tag_id = r[0][0]
            if tag_id:
                rs = store.execute("select distinct(user_id) from me_user_tag where tag_id=%s", tag_id)
                return sorted([cls.get(r[0]) for r in rs if str(r[0]) not in CHART_BLACK_LIST_UIDS], key=attrgetter('score'), reverse=True)
        return []

    @classmethod
    def gets_by_card(cls, card_id, start=0, limit=10):
        r = store.execute("select count(1) user_id from me_like where liker_id=%s", card_id)
        n = r and r[0][0]
        rs = store.execute("select user_id from me_like where liker_id=%s"
            " order by rtime desc limit %s, %s", (card_id, start, limit))
        cids = []
        if rs:
            cids = [str(r[0]) for r in rs]
        return n, [cls.get(i) for i in cids]

    def like(self, liker_id):
        store.execute("replace into me_like(user_id, liker_id) values(%s,%s)", (self.id, liker_id))
        store.commit()
        Notify.new(self.id, liker_id, Notify.TYPE_LIKE)

    def tag(self, tagger_id, tags=[]):
        from webapp.models.tag import Tag
        Tag.tag(self.id, tagger_id, tags=tags)

    @property
    def tags(self):
        from webapp.models.tag import Tag
        return Tag.get_user_tag_names(self.id, self.id)

    def user_tags(self, tagger_id):
        from webapp.models.tag import Tag
        return Tag.get_user_tag_names(self.id, tagger_id)

    @property
    def badages(self):
        return Badage.gets_by_card(self.id)

    @classmethod
    def gets_by_badage(cls, badage_id):
        rs = store.execute("select user_id from me_user_badage where badage_id=%s", badage_id)
        cids = [str(r[0]) for r in rs]
        return [cls.get(i) for i in cids]

    @property
    def ptags(self):
        from webapp.models.tag import Tag
        return Tag.get_user_tags(self.id)

    @property
    def ptag_names(self):
        return [t.name for t in self.ptags]

    @property
    def comment_num(self):
        r = store.execute("select count(1) from me_comment where user_id=%s", self.id)
        if r and r[0]:
            return r[0][0]

    def comment(self, author_id, content):
        store.execute("insert into me_comment(`user_id`,`author_id`,`content`)"
            " values(%s,%s,%s)", (self.id, author_id, content));
        store.commit()
        cid = store.get_cursor(table="me_comment").lastrowid

        Notify.new(self.id, author_id, Notify.TYPE_COMMENT, extra={"comment_id":cid})
        if '@' in content:
            from webapp.models.utils import mention_text
            ret = mention_text(content)
            for b, e, card_id, kind in ret['postions']:
                Notify.new(card_id, author_id, Notify.TYPE_MENTION, extra={"card_id":self.id, "comment_id":cid})

    @property
    def comments(self):
        rs = store.execute("select id, user_id, author_id, content, rtime"
                " from me_comment where user_id=%s order by rtime", self.id)
        return [Comment(*r) for r in rs]

    @property
    def questions(self):
        return Question.gets_by_card(self.id)

    @property
    def answer_num(self):
        return Answer.num_by_card(self.id)

    @property
    def notify_num(self):
        r = store.execute("select count(1) from me_notify where user_id=%s"
            " and flag=%s", (self.id, Notify.FLAG_NEW))
        if r and r[0]:
            return r[0][0]

    @property
    def notifications(self):
        return Notify.gets(self.id)

    def photo_data(self, id, cate=Cate.LARGE):
        if not id:
            id = self.photo_id
        if id > 0:
            return doubanfs.get("/me/card/%s/photo/%s/%s" % (self.id, id, cate))

    @property
    @cache("me-card:{self.id}:score", expire=3600)
    def score(self):
        r = store.execute("select score from me_card where user_id=%s", self.id)
        return r and r[0][0]

    @property
    @cache("me-card:{self.id}:activities", expire=3600)
    def activities(self):
        r = store.execute("select activities from me_card where user_id=%s", self.id)
        return r and r[0][0]

    @classmethod
    @cache("me-card:max-score", expire=3600)
    def max_score(cls):
        r = store.execute("select max(score) from me_card")
        return r and r[0][0]

    @classmethod
    @cache("me-card:max-score", expire=3600)
    def max_activities(cls):
        r = store.execute("select max(activities) from me_card")
        return r and r[0][0]

    @property
    def percent_activities(self):
        MAX = self.max_activities() or 100
        return int(round(float(self.activities)/ MAX, 2)*100)

    @property
    def percent_score(self):
        MAX = self.max_score() or 100
        return int(round(float(self.score)/ MAX, 2)*100)

    @classmethod
    def calculate_score(cls, id):
        d = cls.get(id)
        c = 0
        if d.email:
            c = c + 2
        if d.skype:
            c = c + 2
        if d.alias:
            c = c + 2
        if d.photo_id > 0:
            c = c + 6
        p = d.profile
        sex = int(p.sex)
        if sex == 1:
            c = c + 2
        elif sex == 2:
            c = c + 4
        love = int(p.love)
        if 0 < love < 3:
            c = c + 4
        elif 3 <= love < 5:
            c = c + 1
        m = int(p.marriage)
        if 0 < m < 4:
            c = c + 3*sex
        elif 4 <= m:
            c = c + sex
        if p.birthday:
            if sex == 2:
                now = datetime.now()
                old = now.year - p.birthday.year
                if old < 30:
                    c = c + (35 - old)*2
            else:
                c = c + 4
        if p.zodiac:
            c = c + 1
        if p.astro:
            c = c + 1
        if p.province:
            c = c + 1
        if p.hometown:
            c = c + 1
        if p.weibo:
            c = c + 1
        if p.instagram:
            c = c + 2
        if p.code:
            c = c + 1
        if p.github:
            c = c + 1
        if p.resume:
            c = c + 1
        if p.intro:
            c = c + 4
        #print 'profile score=', c
        now = datetime.now()
        if d.join_time and isinstance(d.join_time, datetime) and d.join_time < now:
            c = c + get_value_by_time(0, 100, d.join_time, 30, -0.2)
        #print 'ctime score=', c
        rs = store.execute("select rtime from me_like where user_id=%s", id)
        for r in rs:
            c = c + get_value_by_time(2, 2, r[0])
        #print 'like score=', c
        rs = store.execute("select rtime from me_comment where user_id=%s", id)
        for r in rs:
            c = c + get_value_by_time(3, 2, r[0])
        #print 'comment score=', c
        rs = store.execute("select rtime from me_user_tag where user_id=%s", id)
        for r in rs:
            c = c + get_value_by_time(3, 2, r[0])
        #print 'tag score=', c
        for tag in d.ptags:
            t = tag.name
            if sex == 1:
                if t in ['少年', '萌', '闷骚', '帅', '傲娇', '四大萌神之一', '老师', '少男杀手', '少女杀手',
                        '单身', '小王子', '正太', '娘', 'gay', '音乐人', '骚年', '很萌']:
                    ##print 'score add tag=', t, ' c=', c
                    c = c + 5
                elif t in ['已婚', '小孩党', '车党']:
                    c = c + 2
            elif sex == 2:
                if t in ['妹子', '萝莉', '萌', '90s', '闷骚', '女神', '美女', '萌妹子', '傲娇', '少女', '实在太漂亮了',
                        '单身', '软妹纸', '温柔如水', '美女不解释', '仙女', '音乐人', '妹纸', '大萝莉', '美少女',
                        '小清新美女', '姐姐']:
                    ##print 'score add tag=', t, ' c=', c
                    c = c + 6
                elif t in ['已婚', '小孩党']:
                    c = c + 3
        #print 'add tag score=', c
        rs = store.execute("select rtime from me_blog, me_blog_like"
                " where user_id=%s and id=blog_id", id)
        for r in rs:
            c = c + get_value_by_time(2, 3, r[0])
        rs = store.execute("select rtime from me_blog as b, me_blog_comment as c"
                " where user_id=%s and b.id=c.blog_id", id)
        for r in rs:
            c = c + get_value_by_time(3, 3, r[0])
        #print 'add blog score=', c
        #metion
        rs = store.execute("select rtime from me_notify where user_id=%s"
            " and ntype=%s", (id, Notify.TYPE_MENTION))
        for r in rs:
            c = c + get_value_by_time(2, 2, r[0])
        rs = store.execute("select rtime from me_notify where user_id=%s"
            " and ntype=%s", (id, Notify.TYPE_BLOG_MENTION))
        for r in rs:
            c = c + get_value_by_time(3, 2, r[0])
        rs = store.execute("select rtime from me_notify where user_id=%s"
            " and ntype=%s", (id, Notify.TYPE_BLOG_COMMENT_MENTION))
        for r in rs:
            c = c + get_value_by_time(3, 3, r[0])
        #print 'mention score=', c
        rs = store.execute("select rtime from me_notify where user_id=%s"
            " and ntype=%s", (id, Notify.TYPE_AWARD_VOTED))
        for r in rs:
            c = c + get_value_by_time(5, 2, r[0])
        #print 'vote score=', c
        rs = store.execute("select rtime from me_notify where user_id=%s"
            " and ntype=%s", (id, Notify.TYPE_CHANGE_PHOTO))
        for r in rs:
            c = c + get_value_by_time(2, 4, r[0])
        #print 'update photo score=', c
        rs = store.execute("select rtime from me_notify where user_id=%s"
            " and ntype=%s", (id, Notify.TYPE_REQUEST_PHOTO))
        for r in rs:
            c = c + get_value_by_time(2, 2, r[0])
        #print 'request photo score=', c

        rs = store.execute("select c.rtime from me_event_photo as p, me_photo_comment as c"
            " where p.author_id=%s and p.id=c.photo_id", id)
        for r in rs:
            c = c + get_value_by_time(2, 2, r[0])

        rs = store.execute("select c.rtime from me_event_photo as p, me_photo_like as c"
            " where p.author_id=%s and p.id=c.photo_id", id)
        for r in rs:
            c = c + get_value_by_time(2, 2, r[0])

        rs = store.execute("select rtime from me_photo_tag where user_id=%s", id)
        for r in rs:
            c = c + get_value_by_time(2, 2, r[0])
        #= =
        if d.uid == 'bear':
            c = c - 100
        return c

    @classmethod
    def gets_by_score(cls, limit=20):
        rs = store.execute("select user_id from me_card where score > 0 and flag=%s"
            " order by score desc limit %s", (cls.FLAG_NORMAL, limit))
        return [cls.get(str(r[0])) for r in rs if str(r[0]) not in CHART_BLACK_LIST_UIDS]

def get_value_by_time(base, value, time, days=2, factor=-0.1):
    if not time or not isinstance(time, datetime):
        return value
    now = datetime.now()
    delta = now - time
    return get_value_by_day(base, value, delta.days/float(days), factor)

def get_value_by_day(base, value, day, factor=-0.1):
    ret = base + value*math.exp(factor*day)
    #print "day=%s, value=%s" % (day, ret)
    return ret
