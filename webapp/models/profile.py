# models.profile
# -*- coding: UTF-8 -*-

from libs import store
from datetime import datetime


class Profile(object):
    def __init__(self, card_id, sex, love, zodiac, astro, birthday, marriage, province, hometown,
                 weibo, instagram, blog, code, github, resume, intro):
        self.card_id = card_id
        try:
            self.sex = int(sex)
            self.love = int(love)
            self.zodiac = int(zodiac)
            self.astro = int(astro)
            self.marriage = int(marriage)
        except:
            self.sex = 0
            self.love = 0
            self.zodiac = 0
            self.astro = 0
            self.marriage = 0

        self.birthday = birthday or ''
        self.province = province
        self.hometown = hometown
        self.weibo = weibo
        self.instagram = instagram
        self.blog = blog
        self.github = github
        self.code = code
        self.resume = resume
        self.intro = intro

    @classmethod
    def get(cls, card_id):
        r = store.execute("select user_id, sex, love, zodiac, astro, birthday, marriage, province, hometown,"
                          " weibo, instagram, blog, code, github, resume, intro from me_profile"
                          " where user_id=%s", card_id)
        if r and r[0]:
            return cls(*r[0])
        else:
            store.execute("insert into me_profile(user_id) values(%s)", card_id)
            store.commit()
            return cls.get(card_id)

    @classmethod
    def update(cls, card_id, sex, love, zodiac, astro, birthday, marriage, province, hometown,
               weibo, instagram, blog, code, github, resume, intro):
        now = datetime.now()
        store.execute(
            "replace into me_profile(user_id, sex, love, zodiac, astro, birthday, marriage, province, hometown,"
            "weibo, instagram, blog, code, github, resume, intro) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,"
            "%s,%s,%s,%s,%s,%s,%s)", (card_id, sex, love, zodiac, astro, birthday, marriage, province, hometown,
                                   weibo, instagram, blog, code, github, resume, intro))
        store.commit()
