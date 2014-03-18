# models.utils
# -*- coding: UTF-8 -*-
import re
from libs import doubandb, doubanfs, Employee, cache, doubanmc, store, User
from quixote.html import html_quote
from config import SITE
from wand.image import Image
from webapp.models.card import Card
from webapp.models.consts import DEFAULT_CONFIG

URL_RE = re.compile(r'(http://|https://|www\.)([a-zA-z0-9\.\-%/\?&_=\+#:~!,\'\*\^$]+)')

class UrlEncode(object):
    def repl(self, match):
        a_protocol = match.group(1)
        a_link = match.group(2)
        url = a_protocol + a_link
        if url.startswith(SITE):
            return '<a href="%s">%s</a>' % (url, url)
        else:
            return '<a href="%s" target="_blank">%s</a>' % (url, url)

    def __call__(self, s):
        return URL_RE.sub(self.repl, s)

url_encode = UrlEncode()

def scale(data, cate, configs):
    with Image(blob=data) as img:
        config = configs[cate]
        #print cate, config
        try:
            cw = int(config['width'])
            ch = int(config['height'])
        except ValueError:
            cw = DEFAULT_CONFIG[cate]['width']
            ch = DEFAULT_CONFIG[cate]['height']

        iw = img.width
        ih = img.height
        cw = min(iw, cw)
        ch = min(ih, ch)
        sc = config['scale']
        #print cw, ch, iw, ih, sc
        if img.mimetype == 'image/gif':
            sc = config['gif_scale']
        if not (max(iw, ih) < min(cw, ch)):
            #以宽度进行等比缩放
            if sc == 'fill-start':
                #print 'fill-start'
                if iw > cw:
                    th = int(ih*cw / float(iw))
                    #print 'resize to', cw, th
                    img.resize(cw, th, "catrom")
            #center crop
            elif sc == 'center-crop':
                #print 'center-crop'
                if iw > cw and ih > ch:
                    #iw/ih <= cw/ch
                    if iw*ch <= cw*ih:
                        th = int(ih*cw / float(iw))
                        #print "to h", th
                        #print "resize to", cw, th
                        img.resize(cw, th, "catrom")
                        ot = (th - ch) % 2
                        dy = (th - ch) / 2
                        #print "dy", dy
                        #print "crop", 0, dy, cw, th - dy
                        img.crop(0, dy, cw, th - dy - ot)
                    else:
                        tw = int(iw*ch / float(ih))
                        #print "to w", tw
                        #print "resize to", tw, ch
                        img.resize(tw, ch, "catrom")
                        ot = (tw - cw) % 2
                        dx = (tw - cw) / 2
                        #print "dx", dx, "ot", ot
                        #print "crop", dx, 0, tw - dx - ot, ch
                        img.crop(dx, 0, tw - dx - ot, ch)
                elif iw > cw and ih <= ch:
                    ot = (iw - cw) % 2
                    dx = (iw - cw) / 2
                    #rint "crop", dx, 0, iw - dx - 1, ch
                    img.crop(dx, 0, iw - dx - ot, ch)
                elif iw <= cw and ih > ch:
                    ot = (ih - ch) % 2
                    dx = (ih - ch) / 2
                    #print "crop", 0, dx, cw, ih - dx
                    img.crop(0, dx, cw, ih - dx - ot)
        #print 'new width', img.width, img.height
        return img.make_blob()

def transfer_user(from_id, to_id):
    from_user = User(id=from_id)
    to_user = User(id=to_id)
    if from_user and to_user:
        from_id = from_user.id
        to_id = to_user.id
        print 'from', from_id, 'to', to_id
        #+----------------+
        #| me_card        |
        print 'trans me_card'
        store.execute("update me_card set user_id=%s, uid=%s, rtime=rtime"
            " where user_id=%s", (to_id, to_user.uid, from_id))
        #| me_comment     |
        print 'trans me_comment'
        store.execute("update me_comment set user_id=%s, rtime=rtime"
            " where user_id=%s", (to_id, from_id))
        store.execute("update me_comment set author_id=%s, rtime=rtime"
            " where author_id=%s", (to_id, from_id))
        #| me_like        |
        print 'trans me_like'
        store.execute("update me_like set user_id=%s, rtime=rtime"
            " where user_id=%s", (to_id, from_id))
        store.execute("update me_like set liker_id=%s, rtime=rtime"
            " where liker_id=%s", (to_id, from_id))
        #| me_notify      |
        print 'trans me_notify'
        store.execute("update me_notify set user_id=%s, rtime=rtime"
            " where user_id=%s", (to_id, from_id))
        store.execute("update me_notify set author_id=%s, rtime=rtime"
            " where author_id=%s", (to_id, from_id))
        #| me_profile     |
        print 'trans me_profile'
        store.execute("update me_profile set user_id=%s, rtime=rtime"
            " where user_id=%s", (to_id, from_id))
        #| me_tag         |
        #| me_user_tag    |
        print 'trans me_user_tag'
        store.execute("update me_user_tag set user_id=%s, rtime=rtime"
            " where user_id=%s", (to_id, from_id))
        store.execute("update me_user_tag set tagger_id=%s, rtime=rtime"
            " where tagger_id=%s", (to_id, from_id))
        #+----------------+
        store.commit()

@cache("me:users:dict", expire=3600)
def get_users_dict():
    r = {}
    rs = store.execute("select uid, user_id from me_card where flag=%s", Card.FLAG_NORMAL)
    uids = []
    for uid, user_id in rs:
        uids.append(str(user_id))
        r[uid.strip().lower()] = str(user_id)
    rs = store.execute("select alias, user_id from me_card where flag=%s", Card.FLAG_NORMAL)
    for alias, user_id in rs:
        if alias:
            r[alias.strip().lower()] = str(user_id)
    for id in uids:
        try:
            if id:
                u = User(id=id)
                if u:
                    r[u.name.strip().lower()] = id
        except:
            pass
    return r

SPACE_TO_NBSP_RE = re.compile(r'^(\s+)')
def covert_space_and_newline(s):
    def _space_to_nbsp(match):
        return ''.join( '&nbsp;' * ( 8 if c == '\t' else 1 ) for c in match.group(1) )

    return '<br>'.join( SPACE_TO_NBSP_RE.sub(_space_to_nbsp, l) for l in s.splitlines() )

MENTION_RE = re.compile(r'(@([^ @]+))|(http://|https://|www\.)([a-zA-z0-9\.\-%/\?&_=\+#:~!,\'\*\^$]+)|#([^@#/\\]+)#')

class MentionText(object):

    def __init__(self):
        self.users_dict = get_users_dict()

    def repl(self, match):
        at, name, protocol, link, topic = match.groups()
        #print 'repl enable_topic=', self.enable_topic
        #print 'mention', at, name, protocol, link, topic
        if at and name:
            user_id = self.users_dict.get(name.lower(), None)
            card = user_id and Card.get(user_id)
            if card:
                return user_id, '<a href="%s">@%s</a>' % (card.path, card.screen_name), 'card'
        if protocol and link:
            url = protocol + link
            if url.startswith(SITE):
                return None, '<a href="%s">%s</a>' % (url, url), 'url'
            else:
                return None, '<a href="%s" target="_blank">%s</a>' % (url, url), 'url'
        if self.enable_topic and topic:
            return topic, '<a href="/topic/%s">#%s#</a>' % (html_quote(topic.upper()), html_quote(topic.upper())), 'topic'
        return None, at or topic, None

    def __call__(self, s, enable_topic=False):
        self.enable_topic = enable_topic
        ret = {}
        r = ''
        pos = []
        b = 0
        e = 0
        for i in MENTION_RE.finditer(s):
            b, e1 = i.span()
            r += html_quote(s[e:b])
            id, replaced, kind = self.repl(i)
            if id and kind:
                pos.append((b, e1, id, kind))
            r += replaced
            e = e1
        r += html_quote(s[e:])
        ret['origin'] = s
        ret['postions'] = pos
        ret['html'] = covert_space_and_newline(r)
        return ret

mention_text = MentionText()

def escape_path(s):
    return s.replace('/',' ')

def unescape_path(s):
    return s.replace(' ','/')
