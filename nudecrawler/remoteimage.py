import PIL
from PIL import Image

import os
from urllib.parse import urlparse
import tempfile
import sys
import requests
import subprocess
import nude
from .exceptions import ProblemImage

# detector_address = 'http://localhost:9191/api/v1/detect'

class RemoteImage:
    def __init__(self, url):        
        self.url = url
        self.path = None
        pr = urlparse(self.url)
        suffix = os.path.splitext(pr.path)[1]
        try:            
            r = requests.get(url, timeout=10)
        except requests.exceptions.RequestException as e:
            raise ProblemImage(f'Requests.exception for {self.url}: {e}')

        # r.raise_for_status()
        if r.status_code != 200:
            raise ProblemImage(f'Bad status {r.status_code} for {self.url}')

        self.threshold = 0.5

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            self.path = tmp.name
            tmp.file.write(r.content)

    def set_threshold(self, thr):
        self.threshold = thr

    def __del__(self):
        if self.path:
            os.unlink(self.path)

    def download(self):
        pass

    def detect_image(self, script):
        """
        new method, using external script
        """

        if script==':nude':
            return nude.is_nude(self.path)

        rc = subprocess.run([script, self.path], env=os.environ.copy())
        if rc.returncode >= 100:
            print("FATAL ERROR")
            sys.exit(1)        
        return bool(rc.returncode)


    def detect_nudity(self):

        try:
            img = Image.open(self.path)
        except PIL.UnidentifiedImageError:
            raise ValueError('Incorrect image')
        w, h = img.size

        if w<200 or h<200:
            # boring! maybe icon
            raise ValueError('Image is too small')

        files = {'image': open(self.path,'rb')}
        try:
            r = requests.post(detector_address,files=files)
        except requests.RequestException as e:
            print(e)
            print("maybe detector not running?")
            print("docker run -d -p 9191:9191 opendating/adult-image-detector")
            print("or add -a to skip filtering")
            sys.exit(1)
        
        # return r.json()['an_algorithm_for_nudity_detection']
        return r.json()['open_nsfw_score'] > self.threshold
    

