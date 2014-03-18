#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson as json
from quixote.errors import TraversalError, AccessError
from libs.template import st, stf

from webapp.models.blog import Blog
from webapp.views import check_access

_q_exports = []

@check_access
def _q_lookup(req, id):
    blog = Blog.get(id)
    if blog:
        if blog.btype == blog.TYPE_THREAD:
            return req.redirect("/thread/%s/" % id)
        return BlogUI(req, blog)
    return TraversalError("no such blog")


class BlogUI(object):
    _q_exports = ['remove']

    def __init__(self, req, blog):
        self.blog = blog

    def _q_index(self, req):
        blog = self.blog
        if req.get_form_var("output", None) == 'json':
            req.response.set_content_type('application/json; charset=utf-8')
            if req.get_form_var("fireworks", None):
                return json.dumps(blog.fireworks_dict())
            return json.dumps(blog.json_dict(req.user))
        return st('/blog/blog.html', **locals())

    def remove(self, req):
        blog = self.blog
        if blog.btype == blog.TYPE_THREAD:
            return req.redirect("/thread/%s/remove" % blog.id)
        if req.user and req.user.id == self.blog.user_id:
            Blog.remove(self.blog.id, req.user.id)
        return req.redirect("/update")
