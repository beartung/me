#!/usr/bin/python
# -*- coding: utf-8 -*-

class User(object):
    def __init__(self, id, email, passwd, session, session_expire_time, ctime, rtime):
        self.id = str(id)
        self.email = email
        self.passwd = passwd
        self.session = session
        self.session_expire_time = session_expire_time
        self.ctime = self.ctime

    @classmethod
    def get(cls, id):
        pass

    @classmethod
    def get_by_email(cls, email):
        pass

    @classmethod
    def register(cls, email, passwd):
        pass

    def login_user(email, passwd):
