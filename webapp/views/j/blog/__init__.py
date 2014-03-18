#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson as json
from quixote.errors import TraversalError, AccessError
from libs.template import st, stf
from libs import publish_channel_msg
from datetime import datetime
from operator import itemgetter, attrgetter
from webapp.models.blog import Blog
from webapp.models.consts import Cate

_q_exports = ['like', 'comment', 'uncomment', 'unlike']

def _q_access(req):
    req.response.set_content_type('application/json; charset=utf-8')

def like(req):
    r = {
        'err':'invalid'
    }
    if req.get_method() == "POST":
        blog_id = req.get_form_var('bid', '')
        single = req.get_form_var('single', '0')
        single = single == '1'
        blog = Blog.get(blog_id)
        if blog and req.user and not blog.is_liked(req.user.id):
            blog.like(req.user.id)
            blog = Blog.get(blog.id)
            r = {
                'err':'ok',
                'inner_html': stf("/blog/utils.html", "blog_ui_inline", b=blog, req=req, single=single),
            }
            for t in blog.topics:
                html = str(stf("/blog/utils.html", "blog_ui_inline", b=blog, single=False, req=req))
                data = {
                        'blog_id': blog.id,
                        'inner_html': html
                        }
                publish_channel_msg('me-topic-%s' % t.id, data)

    return json.dumps(r)


def unlike(req):
    r = {
        'err':'invalid'
    }
    if req.get_method() == "POST":
        blog_id = req.get_form_var('bid', '')
        single = req.get_form_var('single', '0')
        single = single == '1'
        blog = Blog.get(blog_id)
        if blog and req.user and not blog.is_unliked(req.user.id):
            blog.unlike(req.user.id)
            blog = Blog.get(blog.id)
            r = {
                'err':'ok',
                'inner_html': stf("/blog/utils.html", "blog_ui_inline", b=blog, req=req, single=single),
            }
    return json.dumps(r)

def comment(req):
    r = {
        'err':'invalid'
    }
    if req.get_method() == "POST":
        blog_id = req.get_form_var('bid', '')
        blog = Blog.get(blog_id)
        content = req.get_form_var('content', '').strip()
        single = req.get_form_var('single', '0')
        single = single == '1'
        upload_file = req.get_form_var("update_file", None)
        #print 'j comment', blog_id, content
        if blog and req.user and content:
            filename = ''
            ftype = ''
            if upload_file:
                filename = upload_file.tmp_filename
                ftype = upload_file.content_type
            blog.comment(req.user.id, content, filename, ftype)
            blog = Blog.get(blog.id)
            r = {
                'err':'ok',
                'inner_html': stf("/blog/utils.html", "blog_ui_inline", b=blog, req=req, single=single),
            }
            for t in blog.topics:
                html = str(stf("/blog/utils.html", "blog_ui_inline", b=blog, single=False, req=req))
                data = {
                        'blog_id': blog.id,
                        'inner_html': html
                        }
                publish_channel_msg('me-topic-%s' % t.id, data)
    return json.dumps(r)

def uncomment(req):
    r = {
        'err':'invalid'
    }
    if req.get_method() == "POST":
        blog_id = req.get_form_var('bid', '')
        comment_id = req.get_form_var('comment_id', '')
        single = req.get_form_var('single', '0')
        single = single == '1'
        blog = Blog.get(blog_id)
        #print 'j uncomment', comment_id
        if req.user and blog:
            blog.uncomment(req.user.id, comment_id)
            blog = Blog.get(blog.id)
            r = {
                'err':'ok',
                'inner_html': stf("/blog/utils.html", "blog_ui_inline", b=blog, req=req, single=single),
            }
    return json.dumps(r)
