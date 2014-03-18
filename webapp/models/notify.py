# models.notify
# -*- coding: UTF-8 -*-

from operator import itemgetter, attrgetter
from wand.image import Image
from config import DEVELOP_MODE
from datetime import datetime, timedelta
from libs import doubandb, doubanfs, Employee, cache, doubanmc, store, irc_send_message, User
from webapp.models.consts import *
from config import SITE
import simplejson as json

class Notify(object):

    FLAG_NEW = 'N'
    FLAG_READ = 'R'
    FLAG_DELTED = 'D'

    TYPE_LIKE = 'L'
    TYPE_COMMENT = 'C'
    TYPE_MENTION = 'M'
    TYPE_TAG = 'T'
    TYPE_REQUEST_PHOTO = 'R'
    TYPE_REQUEST_CHANGE_PHOTO = 'P'
    TYPE_BADAGE = 'B'
    TYPE_PHOTO_COMMENT = 'D'
    TYPE_PHOTO_COMMENT_MENTION = 'E'
    TYPE_PHOTO_LIKE = 'K'
    TYPE_PHOTO_TAG = 'W'
    TYPE_CHANGE_PHOTO = 'Y'
    TYPE_AWARD_VOTED = 'V'
    TYPE_QUESTION = 'Q'
    TYPE_ANSWER = 'A'

    TYPE_BLOG_LIKE = 'BL'
    TYPE_BLOG_UNLIKE = 'BD'
    TYPE_BLOG_COMMENT = 'BC'
    TYPE_BLOG_REPLY = 'BR'
    TYPE_BLOG_MENTION = 'BM'
    TYPE_BLOG_COMMENT_MENTION = 'BN'

    TYPE_CREATE_GROUP = 'GC'
    TYPE_REC = 'RE'
    TYPE_JOIN_GROUP = 'GJ'
    TYPE_ADD_GROUP = 'GA'
    TYPE_TAG_ADD_GROUP = 'GT'
    TYPE_NEW_THREAD = 'NT'

    ICON_DICT = {
            TYPE_LIKE:'icon-heart',
            TYPE_COMMENT:'icon-comment-alt',
            TYPE_MENTION:'icon-comment-alt',
            TYPE_PHOTO_LIKE: 'icon-thumbs-up',
            TYPE_PHOTO_TAG: 'icon-circle-blank',
            TYPE_PHOTO_COMMENT:'icon-comment-alt',
            TYPE_PHOTO_COMMENT_MENTION:'icon-comment-alt',
            TYPE_TAG:'icon-tags',
            TYPE_REQUEST_PHOTO:'icon-picture',
            TYPE_REQUEST_CHANGE_PHOTO:'icon-picture',
            TYPE_CHANGE_PHOTO: 'icon-camera',
            TYPE_AWARD_VOTED: 'icon-star',
            TYPE_QUESTION: 'icon-question-sign',
            TYPE_ANSWER: 'icon-key',
            TYPE_BADAGE:'icon-trophy',
            TYPE_BLOG_LIKE:'icon-heart',
            TYPE_BLOG_UNLIKE:'icon-thumbs-down',
            TYPE_BLOG_COMMENT:'icon-comment-alt',
            TYPE_BLOG_REPLY:'icon-comment-alt',
            TYPE_BLOG_MENTION:'icon-comment-alt',
            TYPE_BLOG_COMMENT_MENTION:'icon-comment-alt',
            TYPE_ADD_GROUP:'icon-group',
            TYPE_JOIN_GROUP:'icon-group',
            TYPE_CREATE_GROUP:'icon-group',
            TYPE_TAG_ADD_GROUP:'icon-group',
            TYPE_REC:'icon-share',
            TYPE_NEW_THREAD:'icon-file-alt',
    }

    @property
    def icon(self):
        return self.ICON_DICT.get(self.ntype, '')

    def __init__(self, id, card_id, author_id, flag, ntype, extra, rtime):
        self.id = str(id)
        self.card_id = str(card_id)
        self.author_id = str(author_id)
        self.flag = flag
        self.ntype = ntype
        try:
            self.extra = json.loads(extra)
        except:
            self.extra = {}
        self.rtime = rtime

    @classmethod
    def new(cls, card_id, author_id, ntype, extra={}):
        #print 'Notify', card_id, author_id, ntype, extra
        if card_id == author_id:
            return cls.send_blog(card_id, author_id, ntype, extra)
        try:
            extra = json.dumps(extra)
        except:
            extra = "{}"
        store.execute("insert into me_notify(user_id, author_id, ntype, extra)"
                " values(%s,%s,%s,%s)", (card_id, author_id, ntype, extra))
        store.commit()
        nid = store.get_cursor(table="me_notify").lastrowid
        if nid:
            n = cls.get(nid)
            n.send_irc()
            n.to_blog()

    @classmethod
    def get(cls, nid):
        r = store.execute("select id, user_id, author_id, flag, ntype, extra,"
            " rtime from me_notify where id=%s", nid)
        if r:
            return cls(*r[0])

    def to_blog(self):
        self.send_blog(self.card_id, self.author_id, self.ntype, self.extra, self.rtime)

    @classmethod
    def send_blog(cls, card_id, author_id, ntype, extra={}, ctime=None):
        from webapp.models.blog import Blog
        TYPES = [cls.TYPE_LIKE, cls.TYPE_TAG, cls.TYPE_REQUEST_PHOTO,
                cls.TYPE_REQUEST_CHANGE_PHOTO, cls.TYPE_BADAGE, cls.TYPE_AWARD_VOTED, cls.TYPE_QUESTION,
                cls.TYPE_PHOTO_LIKE, cls.TYPE_PHOTO_TAG, cls.TYPE_REC,
                cls.TYPE_CREATE_GROUP, cls.TYPE_TAG_ADD_GROUP, cls.TYPE_JOIN_GROUP, cls.TYPE_ADD_GROUP,
                cls.TYPE_NEW_THREAD,
                ]
        #print 'send_blog', ntype, TYPES, ntype in TYPES
        if ntype in TYPES:
            extra = extra
            extra['author_id'] = author_id
            #print 'do send_blog', ntype
            Blog.new(card_id, Blog.TYPE_NOTIFY, ntype, extra=extra, ctime=ctime)

    def send_irc(self):
        from webapp.models.blog import Blog
        if self.card and self.card and self.card.email:
            message = ''
            if self.ntype == self.TYPE_ADD_GROUP:
                from webapp.models.group import Group
                gid = self.extra.get('group_id', 0)
                group = Group.get(gid)
                if group:
                    message = "#me: 厂工 %s 把你拉进了小组 %s 查看：%s" % (self.author.name, group.name, group.url)
            elif self.ntype == self.TYPE_ANSWER:
                from webapp.models.question import Question
                qid = self.extra.get('question_id', 0)
                bid = self.extra.get('blog_id', 0)
                question = Question.get(qid)
                blog = Blog.get(bid)
                if question and blog:
                    message = "#me: 厂工 %s 回答了你的问题 查看：%s" % (self.author.name, blog.url)
            elif self.ntype == self.TYPE_QUESTION:
                from webapp.models.question import Question
                qid = self.extra.get('question_id', 0)
                question = Question.get(qid)
                if question:
                    if question.is_anonymous:
                        message = "#me: 某厂工问了你一个问题 查看：%s#answers" % (self.card.url)
                    else:
                        message = "#me: 厂工 %s 问了你一个问题 查看：%s#answers" % (self.author.name, self.card.url)
            elif self.ntype == self.TYPE_AWARD_VOTED:
                from webapp.models.badage import Badage, Award
                aid = self.extra.get('badage_id', 0)
                bid = self.extra.get('blog_id', 0)
                blog = Blog.get(bid)
                award = Award.get(aid)
                if award:
                    if blog:
                        message = "#me: 厂工 %s 在评选%s大奖时，投了你一票哦~ 查看：%s" % (self.author.name,
                                award.fullname, blog.url)
                    else:
                        message = "#me: 厂工 %s 在评选%s大奖时，投了你一票哦~ " % (self.author.name,
                                award.fullname)
            elif self.ntype == self.TYPE_PHOTO_LIKE:
                from webapp.models.event import Event, EventPhoto
                pid = self.extra.get('photo_id', 0)
                photo = EventPhoto.get(pid)
                if photo:
                    message = "#me: 厂工 %s 给你上传的照片 + 1了哦~ 查看：%s" % (self.author.name, photo.photo_url)
            elif self.ntype == self.TYPE_PHOTO_TAG:
                from webapp.models.event import Event, EventPhoto
                pid = self.extra.get('photo_id', 0)
                photo = EventPhoto.get(pid)
                if photo:
                    message = "#me: 厂工 %s 在上传的照片圈出了你哦~ 查看：%s" % (self.author.name, photo.photo_url)
            elif self.ntype == self.TYPE_BLOG_LIKE:
                bid = self.extra.get('blog_id', 0)
                blog = Blog.get(bid)
                if blog:
                    message = "#me: 厂工 %s 赞了你的%s~ 查看：%s" % (self.author.name, blog.type_name, blog.url)
            elif self.ntype == self.TYPE_BLOG_UNLIKE:
                bid = self.extra.get('blog_id', 0)
                blog = Blog.get(bid)
                if blog:
                    message = "#me: 你的%s被人踩了哦~ 查看：%s" % (blog.type_name, blog.url)
            elif self.ntype == self.TYPE_BLOG_COMMENT:
                cid = self.extra.get('comment_id', 0)
                bid = self.extra.get('blog_id', 0)
                blog = Blog.get(bid)
                if blog:
                    message = "#me: 厂工 %s 回复了你的%s哦~ 查看：%s#comment_%s" % (self.author.name,
                            blog.type_name, blog.url, cid)
            elif self.ntype == self.TYPE_BLOG_REPLY:
                cid = self.extra.get('comment_id', 0)
                bid = self.extra.get('blog_id', 0)
                blog = Blog.get(bid)
                if blog:
                    message = "#me: 你回复的%s有了新回复哦~ 查看：%s#comment_%s" % (blog.type_name, blog.url, cid)
            elif self.ntype == self.TYPE_BLOG_MENTION:
                bid = self.extra.get('blog_id', 0)
                blog = Blog.get(bid)
                if blog:
                    message = "#me: 厂工 %s 的%s提到了你哦~ 查看：%s" % (self.author.name, blog.type_name, blog.url)
            elif self.ntype == self.TYPE_BLOG_COMMENT_MENTION:
                cid = self.extra.get('comment_id', 0)
                bid = self.extra.get('blog_id', 0)
                blog = Blog.get(bid)
                if blog:
                    message = "#me: 厂工 %s 在 %s 的%s回复里提到了你哦~ 查看：%s" % (self.author.name,
                        blog.owner.name, blog.type_name, blog.url)
            elif self.ntype == self.TYPE_LIKE:
                message = "#me: 厂工 %s ( %s )收藏了你的卡片哦~ 你说他/她/它是不是对你感兴趣？(//▽//)" % (self.author.name,
                        self.author_card.url)
            elif self.ntype == self.TYPE_COMMENT:
                cid = self.extra.get('comment_id', 0)
                message = "#me: 厂工 %s 给你的卡片留言了哦~ 查看：%s#comment_%s" % (self.author.name, self.card.url, cid)
            elif self.ntype == self.TYPE_MENTION:
                cid = self.extra.get('comment_id', 0)
                card_id = self.extra.get('card_id', 0)
                if card_id == self.card_id:
                    message = "#me: 厂工 %s 在给你的卡片留言中提到了你~ 查看：%s#comment_%s" % (self.author.name, self.card.url, cid)
                else:
                    from webapp.models.card import Card
                    card = Card.get(card_id)
                    message = "#me: 厂工 %s 在给 %s 的卡片留言中提到了你了哦~ 查看：%s#comment_%s" % (self.author.name, card.screen_name, card.url, cid)
            elif self.ntype == self.TYPE_PHOTO_COMMENT:
                cid = self.extra.get('comment_id', 0)
                pid = self.extra.get('photo_id', 0)
                from webapp.models.event import Event, EventPhoto
                photo = EventPhoto.get(pid)
                if photo:
                    message = "#me: 厂工 %s 给你上传的照片留言了哦~ 查看：%s%s#comment_%s" % (self.author.name, SITE, photo.path, cid)

            elif self.ntype == self.TYPE_PHOTO_COMMENT_MENTION:
                cid = self.extra.get('comment_id', 0)
                pid = self.extra.get('photo_id', 0)
                from webapp.models.event import Event, EventPhoto
                photo = EventPhoto.get(pid)
                if photo:
                    message = "#me: 厂工 %s 照片里提到你了哦~ 查看：%s%s#comment_%s" % (self.author.name, SITE, photo.path, cid)
            elif self.ntype == self.TYPE_TAG:
                tags = self.extra.get('tags').encode('utf-8')
                message = "#me: 你的卡片有了新的标签(%s)，你猜谁给你打的？ ≖‿≖✧  查看：%s" % (tags, self.card.url)
            elif self.ntype == self.TYPE_REQUEST_PHOTO:
                message = "#me: 厂工 %s ( %s ) 求你的真相照片哦~ 传一张吧，拜托了！m(_ _)m  上传：%s/make" % (self.author.name, self.author_card.url, SITE)
            elif self.ntype == self.TYPE_REQUEST_CHANGE_PHOTO:
                message = "#me: 厂工 %s ( %s )和大家都觉得你的真相照片不真，简直是@#^&*! 换一张吧，拜托了！m(_ _)m  上传：%s/make" % (self.author.name, self.author_card.url, SITE)
            elif self.ntype == self.TYPE_BADAGE:
                from webapp.models.card import Badage
                badage = Badage.get(self.author_id)
                if badage:
                    message = "#me: 你得到了一枚%s徽章哦~ 点击查看：%s/badage/%s" % (badage.name, SITE, badage.name)
            iu = self.card.email.replace('@douban.com','')
            print 'send_irc', iu, message
            try:
                irc_send_message(iu, message)
            except:
                print 'sent irc error!!!'

    @property
    def author(self):
        try:
            return User(id=self.author_id)
        except:
            pass

    @property
    def author_card(self):
        from webapp.models.card import Card
        return Card.get(self.author_id)

    @property
    def card(self):
        from webapp.models.card import Card
        return Card.get(self.card_id)

    @classmethod
    def gets(cls, card_id):
        rs = store.execute("select id, user_id, author_id, flag, ntype, extra,"
            " rtime from me_notify where user_id=%s and flag !=%s"
            " order by id desc", (card_id, cls.FLAG_DELTED))
        return [cls(*r) for r in rs]

    @classmethod
    def read_by_card(cls, card_id):
        store.execute("update me_notify set flag=%s where"
            " user_id=%s and flag=%s", (cls.FLAG_READ, card_id, cls.FLAG_NEW))
        store.commit()

    @classmethod
    def read_by_blog(cls, user_id, blog_id):
        rs = store.execute("select id, extra from me_notify where user_id=%s", user_id)
        for id, extra in rs:
            if blog_id in extra:
                cls.read(id)

    @classmethod
    def read(cls, id):
        store.execute("update me_notify set flag=%s where id=%s", (cls.FLAG_READ, id))
        store.commit()

    def delete(self):
        store.execute("update me_notify set flag=%s where id=%s", (self.FLAG_DELTED, id))
        store.commit()
