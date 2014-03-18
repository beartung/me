# models.question
# -*- coding: UTF-8 -*-

from operator import itemgetter, attrgetter
from webapp.models.consts import ADMINS
from webapp.models.notify import Notify
from libs import store
from libs import doubandb, doubanfs, Employee, cache, doubanmc, store, User
from datetime import datetime, timedelta

class Answer(object):
    def __init__(self, id, blog_id, question_id, author_id, rtime):
        self.id = str(id)
        self.blog_id = str(blog_id)
        self.question_id = str(question_id)
        self.author_id = str(author_id)
        self.rtime = rtime

    @classmethod
    def get(cls, id):
        r = store.execute("select id, blog_id, question_id, author_id, rtime from me_answer where id=%s", id)
        if r:
            return cls(*r[0])

    @classmethod
    def get_by_question(cls, question_id):
        r = store.execute("select id, blog_id, question_id, author_id, rtime from me_answer"
            " where question_id=%s", question_id)
        if r:
            return cls(*r[0])

    @classmethod
    def num_by_card(cls, user_id):
        r = store.execute("select count(id) from me_answer where author_id=%s", user_id)
        return r[0][0]

    @classmethod
    def new(cls, question_id, author_id, content, filename='', ftype=''):
        q = Question.get(question_id)
        if q and q.user_id == author_id:
            blog_id = '0'
            store.execute("insert into me_answer(question_id, author_id, blog_id)"
                " values(%s,%s,%s)", (question_id, author_id, blog_id))
            id = store.get_cursor(table="me_answer").lastrowid
            from webapp.models.blog import Blog
            blog_id = Blog.new(author_id, Blog.TYPE_BLOG, '', content, filename, ftype, extra={'question_id':q.id})
            store.execute("update me_answer set blog_id=%s, rtime=rtime where id=%s", (blog_id, id))
            store.commit()
            Notify.new(q.author_id, q.user_id, Notify.TYPE_ANSWER, extra={"question_id":q.id, "blog_id":blog_id})
            return id

    @property
    def author(self):
        return User(self.author_id)

    @property
    def author_card(self):
        from webapp.models.card import Card
        return Card.get(self.author_id)

    @property
    def blog(self):
        from webapp.models.blog import Blog
        return Blog.get(self.blog_id)

    @property
    def card(self):
        from webapp.models.card import Card
        return Card.get(self.user_id)

class Question(object):
    FLAG_ANONYMOUS = 'A'
    FLAG_NORMAL = 'N'

    def __init__(self, id, content, user_id, author_id, flag, rtime):
        self.id = str(id)
        self.content = content
        self.user_id = str(user_id)
        self.author_id = str(author_id)
        self.flag = str(flag)
        self.rtime = rtime

    @classmethod
    def get(cls, id):
        r = store.execute("select id, content, user_id, author_id, flag, rtime from me_question where id=%s", id)
        if r:
            return cls(*r[0])

    @classmethod
    def gets_by_card(cls, user_id):
        rs = store.execute("select id, content, user_id, author_id, flag, rtime from me_question"
            " where user_id=%s order by rtime desc", user_id)
        if rs:
            return [cls(*r) for r in rs]
        return []

    @property
    def answer(self):
        return Answer.get_by_question(self.id)

    @property
    def is_anonymous(self):
        return self.flag == self.FLAG_ANONYMOUS

    @property
    def title(self):
        return self.content.replace("?","").replace("？", "") + "？"

    @classmethod
    def new(cls, user_id, author_id, content, anonymous):
        if user_id != author_id:
            flag = anonymous and cls.FLAG_ANONYMOUS or cls.FLAG_NORMAL
            store.execute("insert into me_question(user_id, author_id, content, flag)"
                " values(%s,%s,%s,%s)", (user_id, author_id, content, flag))
            id = store.get_cursor(table="me_question").lastrowid
            store.commit()
            Notify.new(user_id, author_id, Notify.TYPE_QUESTION, extra={"question_id":id})
            return id

    @property
    def author(self):
        return User(self.author_id)

    @property
    def card(self):
        from webapp.models.card import Card
        return Card.get(self.user_id)

    @property
    def author_card(self):
        from webapp.models.card import Card
        return Card.get(self.author_id)
