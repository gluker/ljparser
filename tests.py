#!/usr/bin/env python
from parse_comments import search_in_url as parse_comments
from oracle import search_in_url as oracle

test_cases = [
    'http://rusisrael.livejournal.com/283608.html',
    'http://rusisrael.livejournal.com/4366076.html',
    'http://potrebitel-il.livejournal.com/22412050.html',
    'http://dolboeb.livejournal.com/2858081.html',
    'http://dolboeb.livejournal.com/2868126.html',
    'http://tourism-il.livejournal.com/1003133.html',
    'http://rabota-il.livejournal.com/9281433.html',
    'http://rabota-il.livejournal.com/9069326.html',
    'http://potrebitel-il.livejournal.com/22338502.html',
    'http://rabota-il.livejournal.com/712789.html',
    'http://ladies-il.livejournal.com/7098073.html',
    'http://bambik.livejournal.com/2417988.html',
    ]

for case in test_cases:
    print("Trying {}".format(case))
    try:
        stable = oracle(case)
    except Exception as ex:
        print("Oracle felt on {} with {}".format(case,ex))
        break
    try:
        testing = parse_comments(case)
    except Exception as ex:
        print("Test felt on {} with {}".format(case,ex))
        break
    assert parse_comments(case) == oracle(case), "Results don't match"

