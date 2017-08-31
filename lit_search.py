#!/usr/bin/env python
from lxml import etree as ET
import urllib2
import re
from lxml.html import html5parser, fromstring
from lxml.html.soupparser import BeautifulSoup
import json
import random
from pprint import pprint
from lxml.etree import tostring
from itertools import chain
import os

def stringify_children(node):
    parts = ([node.text] +
            list(chain(*([c.text, tostring(c), c.tail] for c in node.getchildren()))) +
            [node.tail])
    # filter removes possible Nones in texts and tails
    return ''.join(filter(None, parts))


def load_paper_acm(acm_key):
    if not os.path.isdir("cache"):
        os.mkdir("cache")
    if not os.path.isdir("cache/acm"):
        os.mkdir("cache/acm")

    if os.path.exists("cache/acm/" + acm_key):
        with open("cache/acm/" + acm_key) as f:
            return f.read()
    else:
        url = "http://dl.acm.org/citation.cfm?id={}&CFID=978416519&CFTOKEN=83774938&preflayout=flat".format(acm_key)
        opener = urllib2.build_opener()
        opener.addheaders = [('User-Agent', "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11")]
        urllib2.install_opener(opener)
        f = urllib2.urlopen(url)
        t = f.read()
        with open("cache/acm/"+acm_key, "w") as f:
            f.write(t)
            return t


def process_paper(acm_key):
    dump = load_paper_acm(acm_key)
    d = fromstring(dump)
    references = d.xpath("//div[@class='flatbody'][3]/table/tr/td[3]/div")
    cited_by = d.xpath("//div[@class='flatbody'][4]/table/tr/td[2]/div")
    
    referenced_papers = []
    skipped_papers = 0
    
    def parse_cites(tags):
        for t in tags:
            paper = dict(text=None,
                        acm_key=None,
                        key=None)

            links = t.xpath("a")
            if len(links) > 0:
                tag = links[0]
                text = stringify_children(tag).strip()
                m = re.search("id=(\d+)", tag.get('href'))
                if m:
                    paper['acm_key'] = m.group(1)
                    paper['key'] = m.group(1)
                    paper['text'] = text
                else:
                    print "failed"
            else:
                tag = t
                text = stringify_children(tag).strip()
                paper['key'] = text
                paper['text'] = text

            referenced_papers.append(paper)

    print "cited_by   = {}".format(len(cited_by))
    print "references = {}".format(len(references))

    
    parse_cites(cited_by)
    parse_cites(references)
    return referenced_papers

    print "skipped_papers={}".format(skipped_papers)
    #parse_cites(cited_by)
    print len(referenced_papers)
    print referenced_papers
    #print cited_by


        
def load_papers(f):
    with open(f) as j:
        return json.load(j)
    
def write_papers(db, f):
    with open(f, "w") as j:
        json.dump(db, j)

def merge_new(new_papers):
    for n in new_papers:
        if n['key'] not in yes_papers and n['key'] not in no_papers:
            #print u"new undecided : {}".format(n['key'])
            undecided_papers[n['key']] = n
            print "+",
        else:
            print ".",
            

def dump_status():
    print """
    yes: {}
    yes frontier: {}
    no: {}
    undecided: {}
    """.format(len(yes_papers),
            len(yes_frontier),
                   len(no_papers),
                   len(undecided_papers))

def snapshot():
    write_papers(yes_papers, "yes_papers.json")
    write_papers(yes_frontier, "yes_frontier.json")
    write_papers(no_papers, "no_papers.json")
    write_papers(undecided_papers, "undecided_papers.json")


def guess(text):
    words = re.split(" |-", text.upper())
    print words
    for i in keywords:
        if i.upper() in words:
            print "========================================"
            print u"auto accepting\n {}".format(text)
            return True

    for p in keyphrases:
        if p.upper().replace("-", " ") in  text.upper().replace("-", " "):
            print "========================================"
            print u"auto accepting\n {}".format(text)
            return True
        
    return False

yes_papers = load_papers("yes_papers.json")
yes_frontier = load_papers("yes_frontier.json")
no_papers = load_papers("no_papers.json")
undecided_papers = load_papers("undecided_papers.json")

def categorize_papers():
    roots = ["195506"]

    for r in roots:
        new = process_paper(r)
        merge_new(new)

    dump_status()
    keywords=[u"ssd",
              u"flash",
              u"NVM",
              u"FTL",
              u"NAND",
              u"NVRAM",
              u"pcm",
              u"MLC",
              u"SLC",
              u"TLC", u"SCM"]

    keyphrases=[u"solid state",
                u"non-volatile",
                u"flash translation layer",
                u"phase change memor",
                u"persistent memory",
                u"storage class memory"]
    for key, paper in yes_frontier.items():
        dump_status()
        new = process_paper(paper['acm_key'])
        merge_new(new)
        del yes_frontier[key]
        snapshot()

    while len(undecided_papers):
        for key, paper in undecided_papers.items():
            dump_status()

            if key in yes_papers or key in no_papers:
                del undecided_papers[key]
                continue

            keep = False

            if guess(paper['text']):
                keep = True
            elif paper['key'] in yes_papers or paper['key'] in no_papers:
                keep = False
            else:
                print paper['text']
                r = raw_input("Keep? ")
                if r in ["y", "Y"]:
                    keep = True

            if keep:
                yes_papers[key] = paper
                if paper['acm_key']:
                    yes_frontier[key] = paper 
            else:
                no_papers[key] = paper
            del undecided_papers[key]

            snapshot()

categorize_papers()
