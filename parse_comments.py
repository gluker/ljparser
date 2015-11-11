#!/usr/bin/env python
from lxml import html
import requests
import re

markup = {
"//div[@id='container']":{
    "dates" : "//abbr/span/text()",
    "links" : "//a[@class='permalink']/attribute::href",
    "comments" : "//div[contains(concat(' ',@class,' '),' comment-body ')]",
    "collapsed_links" : "//a[@class='collapsed-comment-link']/attribute::href",
    "usernames" : "//span[@class='commenter-name']/span/attribute::data-ljuser",
},
"//html[@class='html-schemius html-adaptive']":{
    "dates" : '//span[@class="b-leaf-createdtime"]/text()', 
    "links" : '//a[@class="b-leaf-permalink"]/attribute::href', 
    "comments" : '//div[@class="b-leaf-article"]', 
    "collapsed_links" : "//div[contains(concat(' ',@class,' '),' b-leaf-collapsed ')]"+
        "/div/div/div[2]/ul/li[2]/a/attribute::href",
    "usernames" : "//div[contains(concat(' ',@class,' '),' p-comment ')][@data-full='1']/attribute::data-username",
    "to_visit": "//span[@class='b-leaf-seemore-more']/a/attribute::href",
},
"//div[@align='center']/table[@id='topbox']":{
    "dates" : "//small/span/text()",
    "links" : "//strong/a/attribute::href",
    "comments": "//div[@class='ljcmt_full']/div[2]",
    "collapsed_links" : "//div[starts-with(@id,'ljcmt')][not (@class='ljcmt_full')]/a/attribute::href",
    "usernames" : "//td/span/a/b/text()"
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
        if len(tree.xpath(u))>0:
            xp = m
            break
    cid_pattern = re.compile("[0-9]+$")
    dates = tree.xpath(xp["dates"])
    links = tree.xpath(xp["links"])
    usernames = tree.xpath(xp["usernames"])
    collapsed_links = tree.xpath(xp["collapsed_links"])
    comments_list = tree.xpath(xp["comments"])
    assert all([len(l) == len(dates) for l in [links,usernames,comments_list]]), \
        "got {d} dates, {l} links, {u} usernames, and {c} comments".format(
         d = len(dates), l = len(links), u = len(usernames), c = len(comments_list))
    comments = map(lambda c:" ".join(c.xpath(".//text()")), comments_list)
    dic = {}
    fields = ["link","date","text","username"]
    for link,date,text,username in zip(links,dates,comments,usernames):
        cid = cid_pattern.findall(link)[0]
        dic[cid] = dict(zip(fields,[link,date,text,username]))

    try:
        for link in tree.xpath(xp["to_visit"]):
            collapsed_links.append(link.split("#")[0])
    except:
        pass
    return dic, links, collapsed_links

def search_in_url(post_url):
    visited = set()
    loaded = set()
    unloaded = set()
    unloaded.add(post_url)
    comments = {}
    c_len_old = 0
    page = 2
    while True:
        while len(unloaded)>0:
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
