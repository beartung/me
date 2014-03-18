# coding: utf-8

from quixote.errors import TraversalError

from webapp.models.card import Card
from webapp.models.event import Event, EventPhoto
from webapp.models.consts import Cate
from webapp.models.blog import Blog, BlogComment
from webapp.models.group import Group
from webapp.models.utils import scale

_q_exports = []

SCALES = {
    'cc': 'center-crop',
    'fs': 'fill-start',
}

def _q_lookup(req, name):
    if not ('-' in name and name.lower()[-4:] in ['.jpg','.png','.gif']):
        raise TraversalError("no such photo")
    ftype = name[-3:]
    n = name[:-4]
    if '$' in name:
        n = name[:name.rindex('$')]
    target_id, photo_id, cate = n.split('-')
    print 'p target_id=%s photo_id=%s cate=%s' % (target_id, photo_id, cate)
    data = None

    scale_type = None
    width = None
    height = None

    if cate.startswith("r_"):
        try:
            r, scale_type, sizes = cate.split('_')
            width, height = sizes.split('x')
            width = int(width)
            height = int(height)
            print 'do resize x=%s, y=%s' % (width, height)
        except:
            print 'do resize fail !!!! ', name
        cate = Cate.LARGE

    if target_id.startswith('evc'):
        event = Event.get(target_id.replace('evc',''))
        if event:
            data = event.photo_data(cate)
    elif target_id.startswith('evp'):
        photo = EventPhoto.get(photo_id)
        if photo:
            data = photo.photo_data(cate)
    elif target_id.startswith('bc'):
        blog_comment = BlogComment.get(target_id.replace('bc', ''))
        if blog_comment:
            data = blog_comment.photo_data(cate)
    elif target_id.startswith('b'):
        blog = Blog.get(target_id.replace('b', ''))
        if blog:
            data = blog.photo_data(cate)
    elif target_id.startswith('g'):
        group = Group.get(target_id.replace('g', ''))
        if group:
            data = group.photo_data(cate)
    else:
        if target_id.startswith('_u_'):
            target_id = target_id.replace('_u_', '')
        card = Card.get(target_id)
        if not card:
            card = Card.get_by_ldap(target_id)
        if card:
            data = card.photo_data(photo_id, cate)
    if not data:
        print "no such photo"
        raise TraversalError("no such photo")
    scale_type = SCALES.get(scale_type, None)
    if scale_type:
        configs = {}
        configs[Cate.RESIZE] = {
            'width': width,
            'height': height,
            'scale': scale_type,
            'gif_scale': scale_type,
        }
        data = scale(data, Cate.RESIZE, configs)
    resp = req.response
    resp.set_content_type('image/jpeg')
    resp.set_header('Cache-Control', 'max-age=%d' % (365*24*60*60))
    resp.set_header('Expires', 'Wed, 01 Jan 2020 00:00:00 GMT')
    if 'pragma' in resp.headers:
        del resp.headers['pragma']
    if cate == Cate.ORIGIN:
        resp.set_content_type('application/force-download')
        resp.set_header('Content-Disposition', 'attachment; filename="%s.%s"' % (name, ftype));
    return data
