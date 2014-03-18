# models.badage
# -*- coding: UTF-8 -*-

from operator import itemgetter, attrgetter
from webapp.models.consts import ADMINS
from webapp.models.notify import Notify
from libs import store
from datetime import datetime, timedelta

class Badage(object):
    def __init__(self, id, name, intro, icon, extra, rtime):
        self.id = str(id)
        self.name = name
        self.intro = intro
        self.icon = icon
        self.rtime = rtime
        try:
            self.extra = json.loads(extra)
        except:
            self.extra = {}

    def json_dict(self):
        ret = {}
        ret['id'] = self.id
        ret['name'] = self.name
        ret['icon'] = self.icon
        return ret

    def update(self, name, intro, icon):
        store.execute("update me_badage set name=%s,intro=%s,icon=%s where id=%s", (name, intro, icon, self.id))
        store.commit()

    def update_extra(self, extra):
        self.extra['expire'] = expire
        try:
            extra = json.dumps(self.extra)
        except:
            extra = "{}"
        store.execute("update me_badage set extrea=%s where id=%s", (extra, self.id))
        store.commit()

    @classmethod
    def new(cls, name, intro, icon):
        store.execute("insert into me_badage(name, intro, icon) values(%s, %s, %s)", (name, intro, icon))
        store.commit()

    @property
    def path(self):
        return '/badage/%s' % (self.name)

    @classmethod
    def get(cls, id):
        r = store.execute("select id, name, intro, icon, extra, rtime from me_badage where id=%s", id)
        if r:
            return cls(*r[0])

    @classmethod
    def gets(cls):
        rs = store.execute("select id, name, intro, icon, extra, rtime from me_badage")
        if rs:
            return [cls(*r) for r in rs]
        return []

    @classmethod
    def get_by_name(cls, name):
        r = store.execute("select id, name, intro, icon, extra, rtime from me_badage where name=%s", name)
        if r:
            return cls(*r[0])

    @classmethod
    def add(cls, card_id, badage_id, admin_id):
        if admin_id in ADMINS:
            r = store.execute("select 1 from me_user_badage where user_id=%s and"
                " badage_id=%s", (card_id, badage_id))
            if not r:
                store.execute("insert into me_user_badage(user_id, badage_id)"
                    " values(%s,%s)", (card_id, badage_id))
                store.commit()
                Notify.new(card_id, badage_id, Notify.TYPE_BADAGE)
                return True
        return False

    @classmethod
    def gets_by_card(cls, card_id):
        rs = store.execute("select badage_id from me_user_badage where user_id=%s", card_id)
        return [Badage.get(r[0]) for r in rs]

class Award(object):
    def __init__(self, badage_id, sponsor, num, expire_time, rtime):
        self.badage_id = str(badage_id)
        self.sponsor = sponsor
        self.num = num
        self.expire_time = expire_time
        self.rtime = rtime

    @property
    def is_expired(self):
        return self.expire_time < datetime.now()

    @property
    def badage(self):
        return Badage.get(self.badage_id)

    @property
    def name(self):
        return self.badage.name

    @property
    def days(self):
        return (self.expire_time - self.rtime).days

    @property
    def fullname(self):
        return "%s之%s" % (self.sponsor, self.badage.name)

    @classmethod
    def get(cls, id):
        r = store.execute("select badage_id, sponsor, num, expire_time, rtime from me_award where badage_id=%s", id)
        if r:
            return cls(*r[0])

    @classmethod
    def gets(cls):
        rs = store.execute("select badage_id, sponsor, num, expire_time, rtime from me_award")
        return [cls(*r) for r in rs]

    @classmethod
    def get_actived(cls):
        now = datetime.now()
        r = store.execute("select badage_id from me_award where expire_time>%s order by rtime desc limit 1", now)
        if r:
            return cls.get(r[0][0])

    @classmethod
    def new(cls, badage_name, sponsor, num, expire_days):
        bd = Badage.get_by_name(badage_name)
        if bd:
            now = datetime.now()
            expire_time = now + timedelta(days=expire_days)
            award = cls.get(bd.id)
            if award:
                expire_time = award.rtime + timedelta(days=expire_days)
                now = award.rtime
            store.execute("replace into me_award(badage_id, sponsor, num, expire_time, rtime)"
                    " values(%s,%s,%s,%s,%s)", (bd.id, sponsor, num, expire_time, now))
            store.commit()

    def is_voted(self, card_id, voter_id):
        r = store.execute("select 1 from me_award_vote where badage_id=%s and user_id=%s"
            " and voter_id=%s", (self.badage_id, card_id, voter_id))
        if r and r[0][0]:
            return True
        return False

    def vote_by_user(self, card_id, voter_id):
        if card_id != voter_id:
            store.execute("replace into me_award_vote(badage_id, user_id, voter_id)"
                    " values(%s,%s,%s)", (self.badage_id, card_id, voter_id))
            store.commit()
            Notify.new(card_id, voter_id, Notify.TYPE_AWARD_VOTED, extra={"badage_id":self.badage_id})
