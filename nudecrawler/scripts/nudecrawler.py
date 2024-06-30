#!/usr/bin/env python

import argparse
import datetime
import json
import time
import sys
import os
import shlex
import shutil
import subprocess
import logging


from dotenv import load_dotenv

import nudecrawler 
from .. import Page, Unbuffered, load
from ..page import  get_processed_images, context_fields
from ..version import __version__
from ..cache import cache
# from ..verbose import printv
from ..config import get_args
import nudecrawler.tgru

import transliterate.discover 

transliterate.discover.autodiscover()

stats = {
    'cmd': None,
    'filter': {
        'expr': 'True',
        'min_image_size': None,
        'min_total_images': 0,
        'min_content_length': None,
        'max_pictures': None,
        'image_extensions': None,        
        'max_errors': None
    },
    'uptime': 0,
    'urls': 0,
    'words': 0,
    'word': None,
    'last': {
        'url': None,
        'status': None,
        'detailed': None,
    },
    'last_interesting': {
        'url': None,
        'status': None,
        'detailed': None,
    },
    

    'now': None,
    'processed_images': 0,
    'ignored_pages': 0,
    'found_interesting_pages': 0,
    'found_nude_images': 0,
    'found_new_nude_images': 0,
    'found_new_total_images': 0,
    'resume': dict(),
    'gap_max': 0,
    'gap_url': None,
    'cache_path': None,
    'cache_save': 1
}

previous_content_length = None

stats_file = None
stats_period = 60

stats_next_write = time.time() + stats_period

started = time.time()

logfile: str = None
stop_after = None
stop_each = None
refresh = None
detect_image = None
detect_url = None

#
# page_mintotal = 0

expr = 'True'

nude = 1
video = 1
verbose = False
all_found = True

filter_methods = {
    "true": ("builtin", ":true"),
    "false": ("builtin", ":false"),
    "mudepy": ("builtin", ":nude"),
    "nudenetb": ("builtin", ":nudenet"),
    "aid": ("image", "detect-image-aid"),
    "nsfwapi": ("image", "detect-image-nsfw-api"),
    "nudenet": ("image", "detect-image-nudenet")
}




def analyse(url):

    global stop_after, previous_content_length

    p = Page(url, all_found=all_found,
            detect_url=detect_url, detect_image=detect_image, ignore_content_length=previous_content_length,
            min_images_size=stats['filter']['min_image_size'], 
            image_extensions = stats['filter']['image_extensions'],
            min_total_images=stats['filter']['min_total_images'],
            max_errors=stats['filter']['max_errors'],
            max_pictures=stats['filter']['max_pictures'],
            expr = stats['filter']['expr'], min_content_length=stats['filter']['min_content_length'])

    stats['urls'] += 1
    
    p.check_all()
    
    stats['last']['url'] = url
    stats['last']['status'] = p._status
    stats['last']['detailed'] = p._status_detailed

    stats['found_new_total_images'] += p.new_total_images
    stats['found_new_nude_images'] += p.new_nude_images

    previous_content_length = p.content_length

    if p.status().startswith('INTERESTING'):        
        stats['found_interesting_pages'] += 1
        stats['found_nude_images'] += p.nude_images
        stats['last_interesting']['url'] = url
        stats['last_interesting']['status'] = p._status
        stats['last_interesting']['detailed'] = p._status_detailed

        if logfile:
            with open(logfile, "a") as fh:
                if logfile.endswith('.json') or logfile.endswith('.jsonl'):
                    print(p.as_json(), file=fh)
                else:
                    print(p, file=fh)
    
    if p.status().startswith("INTERESTING") or verbose:
        print(p)

    if p.status().startswith("IGNORED"):
        stats['ignored_pages'] += 1

    save_stats(force=False)

    if stats['cache_path']:
        cache.save_conditional(stats['cache_path'], stats['cache_save'])

    if stop_after is not None and get_processed_images() > stop_after:
        print("Stop/refresh after processed", get_processed_images(), "images...")
        if refresh:
            # print("Refresh:", refresh)
            subprocess.run(refresh)

            # schedule next stop
            stop_after = get_processed_images() + stop_each
        else:
            print("No --refresh, exiting with code 2")
            sys.exit(2)

    return p


def save_stats(force=False):
    global stats_next_write    

    if stats_file is None:
        return

    if time.time() > stats_next_write or force:
        stats['now'] = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        stats['uptime'] = int(time.time() - started)
        stats['processed_images'] = get_processed_images()
        
        stats['cache'] = cache.status()

        with open(stats_file, "w") as fh:
            json.dump(stats, fh, indent=4)
            stats_next_write = time.time() + stats_period

    


def check_word(word, day, fails, 
               resumecount=None):

    global previous_content_length

    word = word.replace(' ','-').translate({ord('ь'): '', ord('ъ'): ''})

    if word.startswith("https://"):
        baseurl = word
    else:
        trans_word = transliterate.translit(word, 'tgru', reversed=True)
        baseurl=f'https://telegra.ph/{trans_word}'


    stats['word'] = word
    stats['words'] += 1

    url=f'{baseurl}-{day.month:02}-{day.day:02}'

    stats['resume']['month'] = day.month
    stats['resume']['day'] = day.day    
    stats['resume']['count'] = resumecount

    previous_content_length = None


    # r = requests.get(url)  
    if not resumecount:
        p = analyse(url)
        #if p.ignore:
        #    return
        c=2
    else:
        c=resumecount
        print(f"Resume from word {word} count {c}")
    
    

    nfails=0    
    while nfails<fails:        
        url=f'{baseurl}-{day.month:02}-{day.day:02}-{c}'        
        p = analyse(url)

        if p.http_code == 404:
            nfails += 1
        else:
            # end of gap
            if nfails>stats['gap_max']:
                stats['gap_max'] = nfails
                stats['gap_url'] = url
            nfails=0

        c+=1
        stats['resume']['count'] = c


def sanity_check(args):
    pass

def load_stats(path):
    global stats
    with open(path) as fh:
        loaded_stats = json.load(fh)
    
    for k in stats:
        if k not in loaded_stats:
            loaded_stats[k] = stats[k]
    
    stats = loaded_stats

def abort(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)

def main():
    global nude, video, verbose, all_found, stats_file, stats, logfile, \
        stop_after, stop_each, detect_image, detect_url,\
        refresh

    words = None
    args = get_args(argv=None, methods_list=', '.join(filter_methods.keys()), context_fields=context_fields)
    sanity_check(args)

    # when fastforward, we go to specific word/day/count quickly
    fastforward = False

    # Disabled logger for nudenet
    logging.getLogger().disabled = True

    if args.unbuffered:
        sys.stdout = Unbuffered(sys.stdout)

    if args.resume:
        if args.workdir:
            args.resume = os.path.join(args.workdir, args.resume)

        print("Resume from", args.resume)
        try:
            load_stats(args.resume)
        except FileNotFoundError as e: 
            abort(f"Missing status file {args.resume}")

        cmd = stats['cmd']
        args = get_args(argv = shlex.split(cmd)[1:])
        fastforward = True
    else:
        stats['cmd'] = shlex.join(sys.argv)

    if args.workdir:
        for attr in ['cache', 'wordlist', 'log', 'resume', 'stats']:
            old = getattr(args, attr)
            if old is not None:                
                new = os.path.join(args.workdir, old)
                setattr(args, attr, new)

    # nude = args.nude
    # video = args.video
    verbose = args.verbose
    all_found = args.all    
    matched_resume = False
    skipped_words = 0
    stop_after = args.stop
    stop_each = args.stop
    refresh = args.refresh
    detect_url = args.detect_url
    detect_image = args.detect_image
    stats['filter']['expr'] = args.expr
    stats['filter']['min_content_length'] = args.min_content_length
    stats['filter']['max_errors'] = args.max_errors
    stats['filter']['max_pictures'] = args.max_pictures
    stats['cache_path'] = args.cache
    stats['cache_save'] = args.cache_save    

    if args.detect:
        try:
            kind, basename = filter_methods[args.detect]
        except KeyError:
            print(f"Do not know detector {args.detect!r}, use one of known detectors: ({ ', '.join(filter_methods.keys()) }) or explicitly specify script with --detect-image or --detect-url")
            sys.exit(1)

        if kind in ['image', 'url']:
            if shutil.which(basename) is None:
                print(f"Cannot find {basename}, maybe not in $PATH?" ,file=sys.stderr)
                sys.exit(1)

        if kind == 'builtin':
            if basename in [':nude', ':nudenet']:
                detect_image = basename
            else:
                detect_url = basename
        elif kind == 'image':
            detect_image = basename
            print(f"# Will use script {shutil.which(basename)} for filtering images")
        elif kind == 'url':
            detect_url = basename
            print(f"# Will use script {shutil.which(basename)} for filtering images")            
    

    # fix arguments
    if not any([detect_image, detect_url, all_found]):        
        print("# No nudity detector (--detect, --detect-url, --detect-image) given, using built-in --detect-image :nude by default")
        detect_image=':nude'

    nudecrawler.verbose.verbose = verbose

    if args.extensions:
        stats['filter']['image_extensions'] = args.extensions
    
    if args.minsize:
        stats['filter']['min_image_size'] = args.minsize * 1024

    if args.total:
        stats['filter']['min_total_images'] = args.total


    if stats['cache_path']:
        if os.path.exists(stats['cache_path']):
            cache.load(stats['cache_path'])
        else:
            print(f"# No cache file {stats['cache_path']}, start with empty cache")

    # processing could start here

    nudecrawler.load()

    # --url1 
    if args.url1:
        p = analyse(args.url1)
        print(p.status())
        for msg in p._log:
            print(" ", msg)
        return

    ## wordlist
    if args.wordlist:
        stats_file = args.stats
        with open(args.wordlist) as fh:
            words = [line.rstrip() for line in fh]
    
    if args.words:
        words = args.words
    
    if not words:
        print("Need either --url1 URL or words like 'nude' or -w wordlist.txt")
        sys.exit(1)

    logfile = args.log

    for w in words:
        if fastforward and not matched_resume:
            if w == stats['resume']['word']:
                matched_resume = True
            else:
                skipped_words += 1
                continue

        stats['resume']['word'] = w


        if fastforward:
            day = datetime.datetime(2020, stats['resume']['month'], stats['resume']['day'])
        elif args.day is None:
            day = datetime.datetime.now()
        else:
            day = datetime.datetime(2020, args.day[0], args.day[1])

        days_tried = 0
        while days_tried < args.days:
            if fastforward:
                resumecount = stats['resume']['count']
            else:
                resumecount = None
            # stop fastforward
            fastforward=False
            check_word(w, day, args.fails, resumecount=resumecount)
            
            days_tried += 1
            day = day - datetime.timedelta(days=1)


    print(f"Finished {len(words)} (skipped {skipped_words}) words in {time.time() - started:.2f} seconds, found {stats['found_interesting_pages']} pages")
    if fastforward and not matched_resume:
        abort(f"Did not found word {stats['resume']['word']}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print("KEYBOARD INTERRUPT")
        print(e)
        save_stats(force=True)
        