
from bs4 import BeautifulSoup
import urllib.request
from urllib.parse import urljoin
from tqdm import tqdm
from .remoteimage import RemoteImage
from .verbose import get_verbose

def trivial_iterator(xx):
    for x in xx:
        yield x

class Page:

    def __init__(self, url, neednnudes=1, neednvideo=1, all_found=False):
        self.url = url
        self.error = False
        self.nban_links = 0
        self.nban_images = 0
        self.nude_images = 0
        self.nonnude_images = 0
        self.total_images = 0
        self.total_video = 0
        self.local_images = 0
        self.local_video = 0
        self.text_found = list()
        self.links = list()
        self.images = list()
        self.videos = list()
        self.all_found = all_found

        self.neednnudes = neednnudes
        self.neednvideo = neednvideo

        try:
            page = urllib.request.urlopen(self.url)
        except urllib.error.URLError:
            self.error = True
            return

        self.contentlength = int(page.headers['content-length'])

        self.soup = BeautifulSoup(page, "html.parser")

    def check_all(self):
        if self.error:
            print("ERROR, do not check")
            return
        self.total_images = len(self.soup.findAll('img'))
        self.total_links = len(self.soup.findAll('a'))

        self.check_images()
        self.check_video()
    

    def check_video(self):
        self.total_video = len(self.soup.findAll('video'))
        for img in self.soup.findAll('video'):
            src = img.get('src')
            if src.startswith('/file/'):
                self.local_video += 1
            else:
                self.videos.append(src)

    def is_nude(self, url):
        try:
            ri = RemoteImage(url)
            if ri.detect_nudity():
                self.nude_images += 1
            else:
                self.nonnude_images += 1
        except Exception as e:
            if get_verbose():
                print(f"Exception with page {self.url}, image {url}")
                print(e)


    def check_images(self):



        def check_1img(img):
            src = img.get('src')
            if src.startswith('/file/'):
                self.local_images += 1
                img_url = urljoin(self.url, src)                
                self.is_nude(img_url)
                
            else:
                img_url = src
                self.images.append(src)
                self.is_nude(src)

        if not self.all_found:
            for img in tqdm(self.soup.findAll('img'), 
                    ascii=" **", desc=self.url, disable=not get_verbose()):
                check_1img(img)



    def status(self):
        if self.error:
            return "ERROR"

        if self.all_found:
            return "INTERESTING (ALL)"

        if self.total_video >= self.neednvideo:
            return "INTERESTING"

        if self.nude_images >= self.neednnudes:
            return "INTERESTING"

        return "???"


    def print(self):
        print(self.status(), self.url)
        if self.all_found:
            print("  Total images:", self.total_images)
        else:
            print("  Nude:",self.nude_images, "non-nude:", self.nonnude_images)
        if self.total_video:
            print("  Total video:", self.total_video)
        print()

