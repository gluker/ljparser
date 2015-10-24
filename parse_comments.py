from time import sleep
from lxml import html
import requests
import re

def parse_comments(post_url):
    markup = {
    "//div[@id='container'][@class='ng-scope']":{
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
        "collapsed_links" : "//div[contains(concat(' ',@class,' '),' b-leaf-collapsed ')]/div/div/div[2]/ul/li[2]/a/attribute::href",
        "usernames" : "//div[contains(concat(' ',@class,' '),' p-comment ')][@data-full='1']/attribute::data-username",
    },
    "//div[@align='center']/table[@id='topbox']":{
        "dates" : "//small/span/text()",
        "links" : "//strong/a/attribute::href",
        "comments": "//div[@class='ljcmt_full']/div[2]",
        "collapsed_links" : "//div[starts-with(@id,'ljcmt')][not (@class='ljcmt_full')]/a/attribute::href",
        "usernames" : "//div[@class='ljcmt_full']/*//a/b/text()"
        }}
    
    def get_from_url(url,dic):
        url = url.split("#")[0]
        if '?' not in url:
            url += "?nojs=1"
        else:
            url=url[:url.index("?")+1]+"nojs=1&"+url[url.index("?")+1:]
        
        page = requests.get(url)
        tree = html.fromstring(page.text)
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

        assert all([len(l) == len(dates) for l in [links,usernames,comments]])
        
        for i in range(len(links)):
            cid = re.findall(cid_pattern,links[i])[0]
            if cid not in dic or not dic[cid]["full"]:
                dic[cid] = {
                    "link" : links[i],
                    "date" : dates[i],
                    "text" : comments[i].text_content(),
                    "username" : usernames[i],
                    "full" : True
                }
        for link in collapsed_links:
            cid = re.findall(cid_pattern,link)[0]
            if cid not in dic:
                dic[cid] = {
                    "link" : link,
                    "full" : False
                }

    def first_unloaded(dic):
        for c in dic:
            if not dic[c]["full"]:
                return dic[c]["link"]
        return None

    comments = {}
    nxt = post_url
    prev = ""
    while True:
        get_from_url(nxt,comments)
        prev = nxt
        nxt = first_unloaded(comments)
        assert nxt_old != nxt #we stuck
        if nxt is None:
            break
        sleep(1)
    return comments

if __name__ == "__main__":
    from sys import argv
    from json import dumps
    print (dumps(parse_comments(argv[1])))

