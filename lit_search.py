#!/usr/bin/env python
from fake_useragent import UserAgent

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
import time
import random
import sys
user_agent = UserAgent().random

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
        sys.stderr.write("h")#print "hit: {}".format(acm_key)
        with open("cache/acm/" + acm_key) as f:
            return f.read()
    else:
        
        #print "miss: {}".format(acm_key)
        delay = random.randrange(10) + random.randrange(10)
        sys.stderr.write("m")#print "{} ".format(delay),
        time.sleep(delay)
        #        url = "http://dl.acm.org/citation.cfm?id={}&CFID=978416519&CFTOKEN=83774938&preflayout=flat".format(acm_key)
        url = "http://dl.acm.org/citation.cfm?id={}&preflayout=flat".format(acm_key)
        print url
        opener = urllib2.build_opener()
        opener.addheaders = [('User-Agent', user_agent)]
        urllib2.install_opener(opener)
        f = urllib2.urlopen(url)
        t = f.read()

        if "Service Temporarily Unavailable" in t:
            raise Exception("Service temporarily unavailable")
        if "ACCESS FORBIDDEN" in t.upper():
            raise Exception("Access forbidden")
        
        with open("cache/acm/"+acm_key, "w") as f:
            f.write(t)
            return t


def process_paper(paper=None, acm_key=None):
    if paper is not None:
        acm_key = paper['acm_key']
        
    dump = load_paper_acm(acm_key)

    if paper:
        paper['bib_stats'] = extract_bib_stats(dump)
        paper['abstract'] = extract_abstract(dump)
        
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
                    print "failed here: {}".format(tag.get('href'))
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

        
def load_papers(f):
    with open(f) as j:
        return json.load(j)
    
def write_papers(db, f):
    with open(f+".new", "w") as j:
        json.dump(db, j, sort_keys=True,
                  indent=4, separators=(',', ': '))
    os.rename(f+".new", f)
    
def merge_new(new_papers):
    for n in new_papers:
        if n['key'] not in yes_papers and n['key'] not in no_papers and n['key'] not in yes_frontier:
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


keywords=[u"ssd",
          u"flash",
          u"NVM",
          u"FTL",
          u"NAND",
          u"NVRAM",
          u"pcm",
          u"pram",
          u"MLC",
          u"STT",
          u"SLC",
          u"TLC", u"SCM"]

keyphrases=[u"solid state",
            u"non-volatile",
            u"flash translation layer",
            u"phase change memor",
            u"persistent memory",
            u"storage class memory"]

def guess(text):
    if text is None:
        return False
    
    words = re.split(" |-|\.|,|;|\t", text.upper())
#    print "|{}|".format(text)
#print words
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
    roots = ["195506",
"3037730",
"3037732",
"3124741",
"3124539",
"3123981",
"3132770",
"3080229",
"3037737",
"3037714",
"3037728",
"3121133",
"2798729",
"3080236",
"2933273",
"3124539",
"3124548",
"2523739",
"3124533",
"3064187",
"3064204",
"3132414",
"3132433",
"3132429",
"3132437",
"3132445",
"3132421",
"3132409",
"3132422",
"2540744",
"3087589",
"2967953",
"2987551",
"2987557",
"2987570",
]
    
    for r in roots:
        new = process_paper(acm_key=r)
        merge_new(new)

    dump_status()

    if True:
        for key, paper in yes_frontier.items():
            dump_status()
            new = process_paper(paper)
            merge_new(new)
            yes_papers[key] = paper
            del yes_frontier[key]
            snapshot()

    def sort_by_cites(x):
        try:
            if int(x[1]['pub_year']) < 2006:
                return 0

            return -int(x[1]['bib_stats']['cites'])
        except:
            return 0
        
    def sort_by_recent(x):
        try:
            return -int(x[1]['pub_year'])
        except:
            return 0
        
    while len(undecided_papers):
        ordered = undecided_papers.items()
        ordered.sort(key=sort_by_cites)
        for key, paper in ordered:
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
                #continue

                print paper.get('abstract')
                print
                print paper['text']
                try:
                    print "Citations: {}".format(paper['bib_stats']['cites'])
                except:
                    pass
                r = raw_input("Keep? ")
                if r in ["y", "Y"]:
                    keep = True

            if keep:
                if paper['acm_key']:
                    yes_frontier[key] = paper 
            else:
                no_papers[key] = paper
            del undecided_papers[key]

            snapshot()
        

            
def populate_cache():
    for key, paper in yes_papers.items() + no_papers.items() + yes_frontier.items():
        #for key, paper in undecided_papers.items() + yes_papers.items() + no_papers.items() + yes_frontier.items():
#    for key, paper in undecided_papers.items():
        #if key != "1884660":
        #    continue
        #print "Got it"
#    for key, paper in yes_papers.items():
        if paper['acm_key'] is not None:
            if update_paper(paper):
                pass
        snapshot()
            

def update_paper(paper):
    try:
        blob = load_paper_acm(paper['acm_key'])
        paper['bib_stats'] = extract_bib_stats(blob)
        paper['abstract'] = extract_abstract(blob)
        paper['pub_year'] = extract_publication_date(blob)
        paper['bibtex'] = load_bibtex(paper)
        #print paper
        return True
    except Exception as e:
        print "error {}".format(e)
        return False


def extract_abstract(blob):
    xml = fromstring(blob)
    t = sorted(xml.xpath('//p'), key=lambda x: 0 if not x.text else -len(x.text))[0]
    return t.text

def extract_publication_date(blob):
    m = re.search("<td nowrap=\"nowrap\">Publication Date</td><td>(\d+)-(\d+)-(\d+)&nbsp;", blob)
    if m:
        return m.group(1)
    else:
        m = re.search("(\d+) Article<br />", blob)
        if m:
            return m.group(1)
        else:
            return None
    
def extract_bib_stats(blob):
    bib_stats=dict(cites="Citation Count: (\d+)",
                   dl="Downloads \(cumulative\): (\d+|n/a)",
                   dl_52="Downloads \(12 Months\): (\d+|n/a)",
                   dl_6="Downloads \(6 Weeks\): (\d+|n/a)")

    stats = {}
    for key, pattern in bib_stats.items():
        #print pattern
        r = re.search(pattern, blob)
        if r.group(1) != "n/a":
            stats[key] = int(r.group(1))
            
    return stats

authors={}

def extract_authors(paper):
    return map(lambda x:x.strip().encode('utf-8'), paper['text'].split(','))


def load_bibtex(paper):
    acm_key = paper['acm_key']
    if not os.path.isdir("cache"):
        os.mkdir("cache")
    if not os.path.isdir("cache/acm"):
        os.mkdir("cache/acm")

    if os.path.exists("cache/acm/" + acm_key + ".bib"):
        sys.stderr.write("HB")#print "hit: {}".format(acm_key)
        with open("cache/acm/" + acm_key + ".bib") as f:
            return f.read()
    else:

        delay = random.randrange(10) + random.randrange(10)
        sys.stderr.write("MB")#print "{} ".format(delay),
        time.sleep(delay)

        url = "http://dl.acm.org/exportformats.cfm?id={}&expformat=bibtex".format(acm_key)
        print url
        opener = urllib2.build_opener()
        opener.addheaders = [('User-Agent', user_agent)]
        urllib2.install_opener(opener)
        f = urllib2.urlopen(url)
        t = f.read()
        r = re.search(u"<PRE id=\"\d+\">(.*)</pre>", t, flags=re.DOTALL);
        if r:
            with open("cache/acm/" + acm_key + ".bib", "w") as f:
                f.write(r.group(1))
            return r.group(1)
        else:
            sys.stderr.write("Failed")


def count_authors(paper):
    for n in extract_authors(paper):
        authors[n] = authors.setdefault(n,0) + 1
    
def test():
    blob = load_paper_acm("2523740")


def best_papers():
    papers = yes_papers.values()

    papers = sorted(papers, key=lambda x: -get_cites(x))
    for p in papers:
        print "{} {} {} {} {}".format(p.get('pub_year'), get_cites(p), cites_per_year(p), p['acm_key'], p['text'].encode('utf-8'))

def get_cites(x):
    return 0 if not x.get('bib_stats') else int(x['bib_stats']['cites'])

def cites_per_year(x):
    year = x.get('pub_year')
    if year is None:
        year = 2017

    years = 2017- int(year) + 1
    return get_cites(x)/years
    
def best_authors():
    papers = yes_papers.values()

    papers = sorted(papers, key=lambda x: -get_cites(x))
    for p in papers[:100]:
        count_authors(p)

    a = zip(authors.values(), authors.keys())
    print "\n".join(map(str,sorted(a, reverse=True)[:50]))

    
def h_index():
    papers = yes_papers.values()
    author_map = {}
    for p in papers:
        for a in extract_authors(p):
            author_map.setdefault(a, []).append(get_cites(p))

    h_index_map = {}
    for a, cite_counts in author_map.items():
        cite_counts.sort(reverse=True)
        for i in range(0, len(cite_counts)):
            if i > cite_counts[i]:
                h_index_map[a] = i-1;
                break

    print "\n".join(map(lambda x:"{}: {}".format(h_index_map[x], x),sorted(h_index_map.keys(), reverse=True, key=lambda x:h_index_map[x])[:50]))

#h_index()
best_authors()
#best_papers()
#categorize_papers()
#test()

#populate_cache()
#snapshot()


