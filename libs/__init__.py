#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import traceback
import json
import os

from sqlstore import SqlStore

PERFORMANCE_METRIC_MARKER = '<!-- _performtips_ -->'

def show_performance_metric(request, output):
    idx = output.find(PERFORMANCE_METRIC_MARKER)
    if idx > 0:
        pt = int((time.time() - request.start_time) * 1000)
        cls = pt > 250 and 'red' or pt > 100 and 'orange' or 'green'
        block = '<li class="hidden-phone"><a style="color:%s"> %d ms </a></li>' % (cls, pt)
        output = (output[:idx] + block + output[idx+len(PERFORMANCE_METRIC_MARKER):])
    return output

store = SqlStore(host='localhost', user='bear', passwd='', db='me')
