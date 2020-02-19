#!/usr/bin/env python
from lxml import html
import requests
import re

markup = {
"//div[@id='container']":{
    'blocks' : '//div[contains(concat(" ",@class," ")," comment ")]',
    "link" : ".//a[@class='permalink']/attribute::href",
    "date" : ".//abbr/span/text()",
    "text" : ".//div[contains(concat(' ',@class,' '),' comment-body ')]//text()",
    "user" : ".//span[@class='commenter-name']/span/attribute::data-ljuser",
    "subject" : ".//div[@class='comment-subject']/text()",
    "collapsed" : "//a[@class='collapsed-comment-link']/attribute::href",
},
"//html[@class='html-schemius html-adaptive']":{
    'blocks' : '//div[contains(concat(" ",@class," ")," comment ")'+
            'and not(contains(concat(" ",@class," ")," b-leaf-collapsed "))]',
    'link' : './/a[@class="b-leaf-permalink"]/attribute::href', 
    'date' : './/span[@class="b-leaf-createdtime"]/text()', 
    'text' : './/div[@class="b-leaf-article"]//text()', 
    'user' : './/span[@class="b-leaf-username-name"]//text()',
    'subject' : './/h4[@class="b-leaf-subject"]//text()',
    "collapsed" : "//div[contains(concat(' ',@class,' '),' b-leaf-collapsed ')]"+
        "/div/div/div[2]/ul/li[2]/a/attribute::href",
    "to_visit": "//span[@class='b-leaf-seemore-more']/a/attribute::href",
},
"//div[@align='center']/table[@id='topbox']":{
    "blocks": "//div[@class='ljcmt_full']",
    "link" : ".//td[@class='social-links']/p/strong/a/attribute::href",
    "date" : ".//small/span/text()",
    "text": "./div[2]//text()",
    "user" : ".//td/span/a/b/text()",
    "subject" : ".//td/h3/text()",
    "collapsed" : "//div[starts-with(@id,'ljcmt')][not(@class='ljcmt_full')]/a/attribute::href",
},
"//html[contains(@class, 'html-s2-no-adaptive')]":{
    "blocks": '//div[starts-with(@id, "ljcmt")]',
    "link" : ".//span[@class='comment-datetimelink']/a[last()]/attribute::href",
    "date" : ".//span[@class='comment-datetimelink']/a/span/text()",
    "text": "./div[2]//text()",
    "user" : ".//div[@class='comment-poster-info']/span/attribute::data-ljuser",
    "subject" : ".//div[contains(concat(' ',@class,' '),' comment-head-in ')]/h3/text()",
    "collapsed" : "//div[starts-with(@id,'ljcmt')][not(@class='ljcmt_full')]/a/attribute::href",
},
"//div[@class='bodyblock']":{
    "blocks": "//div[@class='ljcmt_full']",
    "link" : ".//div[@class='commentLinkbar']/ul/li[last()-1]/a/attribute::href",
    "date" : ".//div[@class='commentHeader']/span[1]/text()",
    "text": ".//div[contains(concat(' ',@class,' '),' commentText ')]//text()",
    "user" : ".//span[@class='ljuser']/span/attribute::data-ljuser",
    "subject" : ".//span[@class='commentHeaderSubject']/text()",
    "collapsed" : "//div[@class='commentHolder']/div[@class='commentText']/a/attribute::href",
}}

def tree_from_url(p_url):
    url = p_url.split("#")[0]
    if '?' not in url:
        url += "?nojs=1"
    else:
        url=url[:url.index("?")+1]+"nojs=1&"+url[url.index("?")+1:]
    page = requests.get(url)
    assert page.status_code == 200
    assert "<title>LiveJournal Bot Policy</title>" not in page.text, "Was banned by LJ"
    return  html.fromstring(page.text)
    
def parse_tree(tree):
    for u, m in markup.items():
        if tree.xpath(u):
            xp = m
            break
    blocks = tree.xpath(xp['blocks'])
    collapsed = tree.xpath(xp['collapsed'])
    cid_pattern = re.compile("[0-9]+$")
    fields = ['link','date','text','user','subject']
    comments = {}
    links = []
    for block in blocks:
        comment = dict(zip(fields,[' '.join(block.xpath(xp[f])).strip() for f in fields]))
        if "".join(comment.values()):
            comments[cid_pattern.findall(comment['link'])[0]] = comment
            links.append(comment['link'])
    try:
        for link in tree.xpath(xp["to_visit"]):
            collapsed.append(link.split("#")[0])
    except:
        pass
    return comments, links, collapsed

def search_in_url(post_url):
    visited = set()
    loaded = set()
    unloaded = set()
    unloaded.add(post_url)
    comments = {}
    c_len_old = 0
    page = 2
    while True:
        while unloaded:
            url = unloaded.pop()
            tree = tree_from_url(url)
            visited.add(url)
            c,l,u = parse_tree(tree)
            comments.update(c)
            loaded.update(l)
            unloaded.update(u)
            unloaded.difference_update(visited)
            unloaded.difference_update(loaded)
        c_len = len(comments)
        if c_len == c_len_old:
            break
        c_len_old = c_len
        unloaded.add(post_url+"?page="+str(page))
        page+=1
    return comments

if __name__ == "__main__":
    from sys import argv
    from json import dumps
    cmnts = search_in_url(argv[1])
    print (dumps(cmnts))
