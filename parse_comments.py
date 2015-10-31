#!/usr/bin/python
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
    assert "<title>LiveJournal Bot Policy</title>" not in page.text
    return  html.fromstring(page.text)
    
def parse_tree(tree):
    for u in markup.keys():
        if len(tree.xpath(u))>0:
            xp = markup[u]
            break
    cid_pattern = re.compile("[0-9]+$")
    dates = tree.xpath(xp["dates"])
    links = tree.xpath(xp["links"])
    usernames = tree.xpath(xp["usernames"])
    collapsed_links = tree.xpath(xp["collapsed_links"])
    comments = tree.xpath(xp["comments"])
    dic = {}
    assert all([len(l) == len(dates) for l in [links,usernames,comments]])
    for i in range(len(links)):
        cid = re.findall(cid_pattern,links[i])[0]
        dic[cid] = {
            "link" : links[i],
            "date" : dates[i],
            "text" : comments[i].text_content(),
            "username" : usernames[i],
        }
    
    try:
        for link in tree.xpath(xp["to_visit"]):
            collapsed_links.append(link.split("#")[0])
    except:
        pass
    return dic, links, collapsed_links

def search_in_url(url):
    visited = set()
    loaded = set()
    unloaded = set()
    unloaded.add(url)
    comments = {}
    while len(unloaded)>0:
        url = unloaded.pop()
        print(url)
        tree = tree_from_url(url)
        visited.add(url)
        c,l,u = parse_tree(tree)
        comments.update(c)
        loaded.update(l)
        unloaded.update(u)
        unloaded.difference_update(visited)
        unloaded.difference_update(loaded)
        print (len(unloaded))
    return comments

if __name__ == "__main__":
    from sys import argv
    from json import dumps
    cmnts = search_in_url(argv[1])
    print (len(cmnts))
    
