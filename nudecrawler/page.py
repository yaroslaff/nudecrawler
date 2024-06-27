
from bs4 import BeautifulSoup
import urllib.request
from urllib.parse import urljoin
from .remoteimage import RemoteImage
from . import verbose
from .verbose import printv
from .exceptions import *
from .cache import cache

from evalidate import Expr, EvalException

import requests
import hashlib
import http
import time
import json


from urllib.parse import urlparse
import subprocess
import sys
import os

#def trivial_iterator(xx):
#    for x in xx:
#        yield x

processed_images = 0
context_fields = ['total_images', 'nude_images', 'nonnude_images', 'new_nude_images', 'new_nonnude_images', 'new_total_images', 'total_video']

def get_processed_images():
    return processed_images

def sha1sum(path):
    sum = hashlib.sha1()
    with open(path, 'rb') as source:
        block = source.read(2**16)
        while len(block) != 0:
            sum.update(block)
            block = source.read(2**16)
    return sum.hexdigest()


class Page:

    def __init__(self, url: str, all_found=False, detect_image=None, min_total_images = 0, min_images_size = 10*1024,
                 image_extensions=None, max_errors = None, max_pictures=None,
                 detect_url=None, min_content_length=None, ignore_content_length=None, expr='True'):
        self.url = url
        self.nban_links = 0
        self.nban_images = 0
        self.nude_images = 0
        self.nonnude_images = 0        
        self.total_images = 0

        # images not found in cache
        self.new_nude_images = 0
        self.new_nonnude_images = 0        
        self.new_total_images = 0

        self.total_video = 0
        self.text_found = list()
        self.links = list()        
        self.images = list()
        self.videos = list()
        self.all_found = all_found
        self.ignore_content_length = ignore_content_length
        
        
        # minor errors
        self.error_counter = 0

        self.detect_image = detect_image
        self.detect_url = detect_url
        self.image_extensions = image_extensions or ['.jpg', '.jpeg']
        self.min_image_size = min_images_size
        self.min_total_images = min_total_images
        self.max_errors = max_errors
        self.max_pictures = max_pictures

        # expr to filter interesing
        self._code = None

        self.http_code = None

        self._ignore = False # Ignore this page, we think it's spam, duplicate        
        self._status = None
        self._status_detailed = None
        self._status_logged = False
        self._log = list()
        self.check_time = None
        self.content_length = None

        # can throw evalidate.EvalExpression here
        # node = Expr(expr).code
        # self._code = compile(node, '<user filter>', 'eval')
        self._code = Expr(expr).code
        
        printv("Processing:", self.url)

        try:
            page = urllib.request.urlopen(self.url)
            self.http_code = page.getcode()
            self.content_length = page.headers.get('content-length')
            if self.content_length is not None:
                self.content_length = int(self.content_length)

            if self.content_length and min_content_length and self.content_length < min_content_length:
                self.ignore(f"content-length {self.content_length} < minimal {min_content_length}")
                return
        except (urllib.error.URLError, ConnectionError, http.client.RemoteDisconnected) as e:
            if hasattr(e, 'status') and e.status == 404:
                # print(e, type(e))
                # silent ignore most usual error (unless verbose)
                printv(url, 404)
                self._status = "IGNORED"
                self._status_detailed = "404"
                self._ignore = True
                self.http_code = e.status
            else:
                if hasattr(e, 'status'):
                    self.http_code = e.status
                self.ignore(f'Exception {e} with {self.url}')            
            return
        self.content_length = page.headers.get('content-length')
        
        if self.ignore_content_length is not None and self.ignore_content_length == self.content_length:
            self.ignore(f"Ignore because matches prev page content-length = {self.content_length}")
            return
        
        self.soup = BeautifulSoup(page, "html.parser")


    def ignore(self, reason):
        self._ignore = True        
        self._status = f"IGNORED"
        self._status_detailed = reason
        printv(f"IGNORE {self.url}, {self._status_detailed}")
        self.log(self._status_detailed)


    def log(self, msg, really=True):
        if not really:
            return        
        self._log.append(msg)

    def check_all(self):
        started = time.time()

        if self._ignore:            
            return
        
        self.total_images = len(self.soup.findAll('img'))
        self.total_links = len(self.soup.findAll('a'))

        self.check_images()
        self.check_video()
    
        self.check_time = round(time.time() - started, 2)
        self.log(f"Check time: {self.check_time}")
        # set status
        self.status()
        

    def check_video(self):
        self.total_video = len(self.soup.findAll('video'))
        for img in self.soup.findAll('video'):
            src = img.get('src')
            self.videos.append(src)

    def error(self, msg):
        self.error_counter += 1
        self.log(f"minor error ({self.error_counter}): {msg}")
        if self.max_errors is not None and self.error_counter > self.max_errors:
            self.ignore(f'Too many minor errors: {self.max_errors}')            

    def prefilter_image(self, url):
        """ True is we should check, False if we can ignore this image"""
        
        if self._ignore:
            return False
        verdict = cache.url2v(url)
        
        if verdict is not None:
            # self.log(f'{url} passed prefilter because cached')
            return True 
        
        path = urlparse(url).path
        ext = os.path.splitext(path)[1]
        if ext not in self.image_extensions:            
            self.log(f"{url} bad extension, ignore")
            return False
        try:
            r = requests.head(url, timeout=1)
        except requests.exceptions.RequestException as e:            
            self.error(f'{url} request exception: {e}')
            return False

        if r.status_code != 200:
            self.error(f"Bad status code: {url} {r.status_code}")
            return False
        try:
            cl = int(r.headers['Content-Length'])
        except KeyError:
            cl = None

        # self.log(f"{url} status:{r.status_code} content-length: {cl}")
        if cl is not None and cl < self.min_image_size:
            self.log(f"Too small image ({int(r.headers['Content-Length'])})")
            return False

        # self.log(f"{url} image passed prefilter")
        return True


    def do_detect_url(self, url):

        if self.detect_url == ':true':
            self.nude_images += 1
            return True
        
        if self.detect_url == ':false':                
            return False            

        rc = subprocess.run([self.detect_url, url])
        if rc.returncode >= 100:
            print("FATAL ERROR")
            sys.exit(1)
        if rc.returncode:
            self.log(f"{url} is nude")
            self.nude_images += 1
        else:
            self.log(f"{url} is NOT nude")
            self.nonnude_images += 1
        
        return 

    def do_detect_image(self, url):
        try:
            ri = RemoteImage(url)
            sum = sha1sum(ri.path)
            verdict = cache.sum2v(sum, url=url)
            if verdict is not None:                    
                if verdict:
                    self.log(f"{url} is nude (cached sum)")
                    self.nude_images += 1
                else:
                    self.log(f"{url} is NOT nude (cached sum)")
                    self.nonnude_images += 1
                return verdict

            verdict = ri.detect_image(self.detect_image)                
            self.new_total_images += 1

            if verdict:
                self.new_nude_images += 1
            else:
                self.new_nonnude_images += 1
            
            cache.register(url, sum, verdict)
            if verdict:
                self.log(f"{url} is nude")
                self.nude_images += 1
            else:
                self.log(f"{url} is NOT nude")                    
                self.nonnude_images += 1
            return 
        except NudeCrawlerException as e:
            print(e)
            return

    def detect_cache_url(self, url):
        verdict = cache.url2v(url)
        if verdict is not None:
            if verdict:
                self.log(f"{url} is nude (cached url)")
                self.nude_images += 1
            else:
                self.log(f"{url} is NOT nude (cached url)")
                self.nonnude_images += 1
        return verdict
        

    def is_nude(self, url):
        os.environ["NUDECRAWLER_PAGE_URL"] = self.url
        os.environ["NUDECRAWLER_IMAGE_URL"] = url

        if self.detect_cache_url(url) is not None:
            return

        if self.detect_url:
            self.do_detect_url(url)
            return

        if self.detect_image:
            try:
                self.do_detect_image(url)
            except Exception as e:
                printv("Broken image:", url)
                print(e)
            return
                
        
        raise(Exception('Need either detect_image or detect_url or all'))

    def check_images(self):
        global processed_images

        image_list = [ urljoin(self.url, img.get('src')) for img in self.soup.findAll('img') ]
        self.log(f"total images on page: {len(image_list)}")
        
        if len(image_list) < self.min_total_images:
            self.ignore(f'Skip because total images {len(image_list)} < {self.min_total_images}')
            return
        
        image_list = list(filter(None, [ url if self.prefilter_image(url) else None for url in image_list ]))

        if self._ignore:            
            return

        self.log(f"total prefiltered images on page: {len(image_list)}")
        if len(image_list) < self.min_total_images:            
            self.ignore(f'Skip because total prefiltered images {len(image_list)} < {self.min_total_images}')
            return

        if not self.all_found:
            for url in image_list[:self.max_pictures]:
                self.is_nude(url)
                processed_images += 1


    def status(self):        

        if not self._status_logged:
            self._status_logged = True
            makelog = True
        else:
            makelog = False
        
        if self._ignore:
            return f"{self._status} ({self._status_detailed})"

        self._status_detailed = f"total: {self.total_images} (min: {self.min_total_images}) " \
                    f"nude: {self.nude_images}"

        self._status_detailed += f" Cache new/nude: {self.new_total_images}/{self.new_nude_images}"

        if self.total_video:
            self._status_detailed += f" video: {self.total_video}"
        self._status_detailed += f" ({self.check_time}s)"
        
        self.log(self._status_detailed, makelog)

        if self.all_found:
            self._status = "INTERESTING (ALL)"
            self.log(self._status, makelog)        
            return self._status

        # Interesting or not? use evalidate
        ctx = dict()
        for field in context_fields :
            ctx[field] = getattr(self, field)
        r = eval(self._code, ctx.copy())
        if r:
            self._status = f'INTERESTING'
            self.log(self._status, makelog)        
            return self._status            


        self._status = "???"
        self.log(self._status, makelog)        
        return self._status            

    def as_json(self):
        j = dict()
        j['status'] = self.status()

        for attr in ['url', 'total_images', 'nude_images', 'new_nude_images', 'nonnude_images', 'new_nonnude_images', 'total_video']:
            j[attr] = getattr(self, attr)

        return json.dumps(j)

    def __str__(self):
        
        text = ''
        
        text += f'{self.status()} {self.url} ({self.check_time}s)\n'

        if self.all_found:
            text += f"  Total images: {self.total_images}\n"
        else:
            text += f"  Nude: {self.nude_images} ({self.new_nude_images} new) non-nude: {self.nonnude_images} ({self.new_nonnude_images} new)\n"
        
        #if self.new_nude_images or self.new_nonnude_images:
        #    text += f"  New nude {self.new_nude_images} non-nude {self.new_nonnude_images}\n"
                
        if self.total_video:
            text += f"  Total video: {self.total_video}\n"
        
        return text

