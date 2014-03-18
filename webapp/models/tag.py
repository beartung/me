# models.tag
# -*- coding: UTF-8 -*-

from libs import store
from webapp.models.notify import Notify
from webapp.models.utils import escape_path, unescape_path

class Tag(object):

    def __init__(self, id, name, count):
        self.id = str(id)
        self.name = name
        self.count = count

    def json_dict(self, user):
        ret = {}
        ret['id'] = self.id
        ret['uid'] = escape_path(self.name)
        ret['name'] = self.name
        ret['count'] = self.count
        return ret

    @property
    def path(self):
        return '/tag/%s' % escape_path(self.name)

    @classmethod
    def tag(cls, card_id, tagger_id, tags=[]):
        rs = store.execute("select tag_id from me_user_tag where user_id=%s and tagger_id=%s"
            " order by tag_id", (card_id, tagger_id))
        old_tag_ids = [str(r[0]) for r in rs]
        #print 'old tag ids', old_tag_ids
        store.execute("delete from me_user_tag where user_id=%s and tagger_id=%s", (card_id, tagger_id))
        for t in tags:
            if t:
                r = store.execute("select id from me_tag where name=%s", t)
                if r and r[0]:
                    tag_id = r[0][0]
                else:
                    store.execute("insert into me_tag(name) values(%s)", t)
                    tag_id = store.get_cursor(table="me_tag").lastrowid
                if tag_id:
                    store.execute("replace into me_user_tag(user_id, tagger_id, tag_id)"
                        " values(%s,%s,%s)", (card_id, tagger_id, tag_id))
        store.commit()
        rs = store.execute("select tag_id from me_user_tag where user_id=%s and tagger_id=%s"
            " order by tag_id", (card_id, tagger_id))
        new_tag_ids = [str(r[0]) for r in rs]
        diff_tag_ids = list(set(new_tag_ids) - set(old_tag_ids))
        #print 'new tag ids', new_tag_ids
        if diff_tag_ids and card_id != tagger_id:
            diff_tags = [cls.get(i).name for i in diff_tag_ids]
            Notify.new(card_id, tagger_id, Notify.TYPE_TAG, extra={"tags":' '.join(diff_tags)})

    @classmethod
    def gets(cls, count=3):
        rs = store.execute("select s.id, s.name, s.c from"
            " (select t.id, name, count(t.id) as c from me_tag as t, me_user_tag as ut"
            " where t.id=ut.tag_id group by t.id) as s where s.c > %s order by s.c desc", count)
        return [cls(*r) for r in rs]

    @classmethod
    def get_user_tags(cls, card_id):
        """ tags exclude self tags"""
        rs = store.execute("select tag_id, name, count(1) as c from me_tag as t,"
            " me_user_tag as ut where user_id=%s and ut.tagger_id!=%s"
            " and t.id=ut.tag_id group by tag_id order by c desc, tag_id", (card_id, card_id))
        return [cls(*r) for r in rs]

    @classmethod
    def get_group_tags(cls, group_id):
        rs = store.execute("select t.id, name, count(1) from me_tag as t, me_group_tag as ut"
            " where ut.group_id=%s and t.id=ut.tag_id group by tag_id", group_id)
        return [cls(*r) for r in rs]

    @classmethod
    def get_taggers(cls, uid, tag):
        from webapp.models.card import Card
        d = Card.get(uid)
        t = cls.get_by_name(tag)
        if t and d:
            rs = store.execute("select tagger_id from me_user_tag where user_id=%s"
                " and tag_id=%s", (d.id, t.id))
            return [Card.get(str(r[0])) for r in rs]
        return []

    @classmethod
    def get_by_name(cls, name):
        r = store.execute("select id, name, count(1) from me_tag where name=%s", name)
        if r:
            return cls(*r[0])

    @classmethod
    def get(cls, id):
        r = store.execute("select id, name, count(1) from me_tag where id=%s", id)
        if r:
            return cls(*r[0])

    @classmethod
    def get_user_tag_names(cls, card_id, tagger_id):
        rs = store.execute("select name from me_tag as t, me_user_tag as ut"
            " where ut.user_id=%s and ut.tagger_id=%s and t.id=ut.tag_id"
            " order by ut.rtime desc", (card_id, tagger_id))
        return [r[0] for r in rs]
