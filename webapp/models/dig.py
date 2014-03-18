# models.dig
# -*- coding: UTF-8 -*-

from libs import store
from operator import itemgetter, attrgetter
from webapp.models.card import Card
from webapp.models.consts import *
from webapp.models.notify import Notify

class Dig(object):

    @classmethod
    def basic_result(cls):
        ret = {}
        r = store.execute("select count(1) user_id from me_card where flag=%s", Card.FLAG_NORMAL)
        ret['n_card'] = r and r[0][0]
        r = store.execute("select count(1) user_id from me_card where email !='' and flag=%s", Card.FLAG_NORMAL)
        ret['n_basic_card'] = r and r[0][0]
        r = store.execute("select count(1) user_id from me_card where photo > 0 and flag=%s", Card.FLAG_NORMAL)
        ret['n_photo_card'] = r and r[0][0]
        return ret

    @classmethod
    def gossip_result(cls):
        ret = {}
        r = store.execute("select user_id from me_card where join_time > '2006-01-09'"
                " and flag=%s order by join_time limit 1", Card.FLAG_NORMAL)
        if r and r[0]:
            ret['first_employee'] = Card.get(r[0][0])

        r = store.execute("select user_id from me_card where user_id > 1000001"
                " and flag=%s order by user_id limit 1", Card.FLAG_NORMAL)
        if r and r[0]:
            ret['first_register'] = Card.get(r[0][0])

        r = store.execute("select user_id from (select user_id, count(user_id) as c from me_like"
                " group by user_id) as s order by s.c desc limit 1")
        if r and r[0]:
            ret['likest_card'] = Card.get(r[0][0])

        r = store.execute("select user_id from (select user_id, count(user_id) as c from me_question"
                " group by user_id) as s order by s.c desc limit 1")
        if r and r[0]:
            ret['question_card'] = Card.get(r[0][0])

        r = store.execute("select user_id from (select user_id, count(user_id) as c from me_comment"
                " group by user_id) as s order by s.c desc limit 1")
        if r and r[0]:
            ret['commentest_card'] = Card.get(r[0][0])

        r = store.execute("select user_id from (select user_id, count(tag_id) as c from me_user_tag"
                " group by user_id) as s order by s.c desc limit 1")
        if r and r[0]:
            ret['taggest_card'] = Card.get(r[0][0])

        rs = store.execute("select s.name, s.c from (select name, count(tag_id) as c from me_tag as t, me_user_tag as ut"
                " where t.id=ut.tag_id group by t.id) as s order by s.c desc limit 5")
        ret['hotest_tags'] = rs

        r = store.execute("select user_id from (select user_id, count(user_id) as c from me_user_badage"
                " group by user_id) as s order by s.c desc limit 1")
        if r and r[0]:
            ret['badagest_card'] = Card.get(r[0][0])

        r = store.execute("select user_id, s.c from (select user_id, count(user_id) as c from me_notify"
                " where ntype=%s group by user_id) as s order by s.c desc limit 1", Notify.TYPE_REQUEST_PHOTO)
        if r and r[0]:
            ret['most_request_photo_card'] = (Card.get(r[0][0]), r[0][1])

        r = store.execute("select user_id, s.c from (select user_id, count(user_id) as c from me_notify"
                " where ntype=%s group by user_id) as s order by s.c desc limit 1", Notify.TYPE_REQUEST_CHANGE_PHOTO)
        if r and r[0]:
            ret['most_request_change_photo_card'] = (Card.get(r[0][0]), r[0][1])

        return ret

    @classmethod
    def all_hometowns(cls):
        rs = store.execute("select distinct(hometown) from me_profile where hometown!=''")
        return [(r[0]) for r in rs]

    @classmethod
    def zodiac_distribution(cls):
        r = store.execute("select count(user_id) from me_profile where zodiac > 0")
        total = r and r[0][0]
        rs = store.execute("select zodiac, count(user_id) from me_profile where zodiac > 0 group by zodiac")
        ret = sorted([(int(z), ZODIACS[int(z)][1], c, c*100.0/total) for z, c in rs])
        return total, ret

    @classmethod
    def astro_distribution(cls):
        r = store.execute("select count(user_id) from me_profile where astro > 0")
        total = r and r[0][0]
        rs = store.execute("select astro, count(user_id) from me_profile where astro > 0 group by astro")
        ret = sorted([(int(z), ASTROS[int(z)][1], c, c*100.0/total) for z, c in rs])
        return total, ret

    @classmethod
    def province_distribution(cls):
        r = store.execute("select count(user_id) from me_profile where province != ''")
        total = r and r[0][0]
        rs = store.execute("select province, count(user_id) from me_profile where province != '' group by province")
        ret = sorted([(c, c*100.0/total, n) for n, c in rs], reverse=True)
        return total, ret

    @classmethod
    def girl_chart(cls):
        ids = {}
        for d in Card.gets_by_tag('萌'):
            ids[d.id] = 1
        for d in Card.gets_by_tag('单身'):
            n = ids.get(d.id, 0)
            ids[d.id] = n + 1
        for d in Card.gets_by_tag('妹子'):
            n = ids.get(d.id, 0)
            ids[d.id] = n + 1
        for d in Card.gets_by_tag('萝莉'):
            n = ids.get(d.id, 0)
            ids[d.id] = n + 1
        for d in Card.gets_by_tag(''):
            n = ids.get(d.id, 0)
            ids[d.id] = n + 1
        rs = store.execute("select user_id from me_profile where flag=N and sex=2 and marriage in (1, 2, 12)")
        for r in rs:
            i = str(r[0])
            n = ids.get(i, 0)
            ids[i] = n + 2
        love_cards = [Card.get(i) for i, n in ids.iteritems() if n > 1]
        love_cards = [d for d in love_cards if ('汉子' not in ' '.join(d.ptag_names) and d.profile.sex != 1)]
        love_cards = sorted(love_cards, key=attrgetter('score'), reverse=True)
        return love_cards

    @classmethod
    def boy_chart(cls):
        ids = {}
        for d in Card.gets_by_tag('萌'):
            ids[d.id] = 1
        for d in Card.gets_by_tag('单身'):
            n = ids.get(d.id, 0)
            ids[d.id] = n + 1
        for d in Card.gets_by_tag('少年'):
            n = ids.get(d.id, 0)
            ids[d.id] = n + 1
        for d in Card.gets_by_tag('gay'):
            n = ids.get(d.id, 0)
            ids[d.id] = n + 1
        for d in Card.gets_by_tag('娘'):
            n = ids.get(d.id, 0)
            ids[d.id] = n + 1
        rs = store.execute("select user_id from me_profile where flag=N and sex=1 and marriage in (1, 2, 12)")
        for r in rs:
            i = str(r[0])
            n = ids.get(i, 0)
            ids[i] = n + 2
        love_cards = [Card.get(i) for i, n in ids.iteritems() if n > 1]
        love_cards = [d for d in love_cards if d.profile.sex != 2]
        love_cards = sorted(love_cards, key=attrgetter('score'), reverse=True)
        return love_cards
