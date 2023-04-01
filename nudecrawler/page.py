
from bs4 import BeautifulSoup
import urllib.request
from urllib.parse import urljoin
from .remoteimage import RemoteImage
from .verbose import get_verbose
from .exceptions import *
from .cache import cache
import requests
import hashlib
import http

from urllib.parse import urlparse
import subprocess
import sys
import os

def trivial_iterator(xx):
    for x in xx:
        yield x

processed_images = 0

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

    def __init__(self, url, neednnudes=1, neednvideo=1, all_found=False, threshold=0.5, detect_image=None, detect_url=None, ignore_content_length=None):
        self.url = url
        self.error = False
        self.error_reason = None
        self.nban_links = 0
        self.nban_images = 0
        self.nude_images = 0
        self.nonnude_images = 0
        self.total_images = 0
        self.total_video = 0
        self.text_found = list()
        self.links = list()        
        self.images = list()
        self.videos = list()
        self.all_found = all_found
        self.ignore_content_length = ignore_content_length
        self.ignore = False # Ignore this page, we think it's spam

        self.neednnudes = neednnudes
        self.neednvideo = neednvideo
        self.threshold = threshold        

        self.detect_image = detect_image
        self.detect_url = detect_url
        self.image_extensions = ['.jpg', '.jpeg']
        self.image_minsize = 10*1024
        self.need_total = 1

        self._status = None
        self._status_detailed = None
        self._status_logged = False
        self._log = list()

        try:
            page = urllib.request.urlopen(self.url)
        except (urllib.error.URLError, ConnectionError, http.client.RemoteDisconnected) as e:
            self.error = True
            self.error_reason = f'Exception {e} with {self.url}'
            return
        self.content_length = page.headers.get('content-length')


        if self.ignore_content_length is not None and self.ignore_content_length == self.content_length:
            self.ignore = True
            self._status = f"IGNORED"
            self._status_detailed = f"Ignore because matches prev page content-length = {self.content_length}"
            if get_verbose:
                print("IGNORE", self.url, self._status_detailed)
            self.log(self._status_detailed)
            return
        
        self.soup = BeautifulSoup(page, "html.parser")

    def log(self, msg, really=True):
        if not really:
            return        
        self._log.append(msg)

    def check_all(self):
        if self.error:
            print("ERROR, do not check")
            return
        
        if self.ignore:
            return

        self.total_images = len(self.soup.findAll('img'))
        self.total_links = len(self.soup.findAll('a'))

        if get_verbose():
            print(self.url)

        self.check_images()
        self.check_video()
    
        # set status
        self.status()

        if get_verbose():
            # print quick summary
            print("  ", self._status, self._status_detailed)

    def check_video(self):
        self.total_video = len(self.soup.findAll('video'))
        for img in self.soup.findAll('video'):
            src = img.get('src')
            self.videos.append(src)

    def prefilter_image(self, url):

        verdict = cache.url2v(url)

        if verdict is not None:
            if verdict:
                self.log(f"{url} is nude (cached url)")
                self.nude_images += 1
            else:
                self.log(f"{url} is NOT nude (cached url)")
                self.nonnude_images += 1
            return verdict

        path = urlparse(url).path
        ext = os.path.splitext(path)[1]
        if ext not in self.image_extensions:
            self.log(f"{url} bad extension, ignore")
            return False
        try:
            r = requests.head(url, timeout=5)
        except requests.exceptions.RequestException as e:
            self.log(f'{url} request exception: {e}')
            return False

        if r.status_code != 200:
            self.log(f"Bad status code: {r.status_code}")
            return False
        try:
            cl = int(r.headers['Content-Length'])
        except KeyError:
            cl = None

        self.log(f"{url} status:{r.status_code} content-length: {cl}")
        if cl is not None and cl < self.image_minsize:
            self.log(f"Too small image ({int(r.headers['Content-Length'])})")
            return False

        self.log(f"{url} image passed prefilter")
        return True


        

    def is_nude(self, url):
        os.environ["NUDECRAWLER_PAGE_URL"] = self.url
        os.environ["NUDECRAWLER_IMAGE_URL"] = url

        if self.detect_url:
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

        if self.detect_image:
            try:
                ri = RemoteImage(url)
                sum = sha1sum(ri.path)
                verdict = cache.sum2v(sum)
                if verdict is not None:
                    if verdict:
                        self.log(f"{url} is nude (cached sum)")
                        self.nude_images += 1
                    else:
                        self.log(f"{url} is NOT nude (cached sum)")
                        self.nonnude_images += 1

                    return verdict

                verdict = ri.detect_image(self.detect_image)
                self.log(f"register verdict {verdict} {url} {sum}")
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
        
        raise(Exception('Need either detect_image or detect_url or all'))

    def check_images(self):
        global processed_images

        image_list = [ urljoin(self.url, img.get('src')) for img in self.soup.findAll('img') ]
        self.log(f"total images on page: {len(image_list)}")
        
        if len(image_list) < self.need_total:
            self.log(f'Skip because total images {len(image_list)} < {self.need_total}')
            return
        
        image_list = list(filter(None, [ url if self.prefilter_image(url) else None for url in image_list ]))
        self.log(f"total prefiltered images on page: {len(image_list)}")
        if len(image_list) < self.need_total:
            self.log(f'Skip because total prefiltered images {len(image_list)} < {self.need_total}')
            return

        if not self.all_found:
            #for url in tqdm(image_list, 
            #        ascii=" **", desc=self.url, disable=not get_verbose()):

            for url in image_list:
                self.is_nude(url)
                processed_images += 1


    def status(self):
        

        if not self._status_logged:
            self._status_logged = True
            makelog = True
        else:
            makelog = False
        
        if self.error:
            self.log(f"ERROR: {self.error_reason}", makelog)            
            self._status = "ERROR"
            return "ERROR"

        if self.ignore:
            return self._status

        self._status_detailed = f"total: {self.total_images} (need: {self.need_total}) nude: {self.nude_images} "\
                    f"({self.neednvideo}) video: {self.total_video} ({self.neednvideo})"
        
        self.log(self._status_detailed, makelog)

        if self.all_found:
            self._status = "INTERESTING (ALL)"
            self.log(self._status, makelog)        
            return self._status

        if self.total_video >= self.neednvideo:
            self._status = f"INTERESTING ({self.total_video} video)"
            self.log(self._status, makelog)        
            return self._status            

        if self.nude_images >= self.neednnudes:
            self._status = f"INTERESTING ({self.nude_images} nudes)"
            self.log(self._status, makelog)        
            return self._status            

        self._status = "???"
        self.log(self._status, makelog)        
        return self._status            

    def __str__(self):
        
        text = ''
        
        text += f'{self.status()} {self.url}\n'

        if self.all_found:
            text += f"  Total images: {self.total_images}\n"
        else:
            text += f"  Nude: {self.nude_images} non-nude: {self.nonnude_images}\n"
        if self.total_video:
            text += f"  Total video: {self.total_video}\n"
        
        return text

