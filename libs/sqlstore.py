#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb
import re

SQL_PATTERNS = {
    "select": re.compile(r'select\s.*?\sfrom\s+`?(?P<table>\w+)`?', re.I|re.S),
    "insert": re.compile(r'insert\s+(ignore\s+)?(into\s+)?`?(?P<table>\w+)`?', re.I),
    "update": re.compile(r'update\s+(ignore\s+)?`?(?P<table>\w+)`?\s+set', re.I),
    "replace": re.compile(r'replace\s+(into\s+)?`?(?P<table>\w+)`?', re.I),
    "delete": re.compile(r'delete\s+from\s+`?(?P<table>\w+)`?', re.I),
}

class SqlStore(object):

    def __init__(self, host='', user='', passwd='', db=''):
        self.conn = MySQLdb.connect(host, user, passwd, db)
        self.cursor = self.conn.cursor()

    def parse_execute_sql(self, sql):
        sql = sql.lstrip()
        cmd = sql.split(' ', 1)[0].lower()
        if cmd not in SQL_PATTERNS:
            raise Exception, 'SQL command %s is not yet supported' % cmd
        match = SQL_PATTERNS[cmd].match(sql)
        if not match:
            raise Exception, sql
        return cmd

    def execute(self, sql, args=()):
        cmd = self.parse_execute_sql(sql)
        ret = self.cursor.execute(sql, args)
        if cmd == 'select':
            return self.cursor.fetchall()
        else:
            if cmd == 'insert' and self.cursor.lastrowid:
                ret = self.cursor.lastrowid
            return ret

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()
