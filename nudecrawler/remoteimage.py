import PIL
from PIL import Image

import os
from urllib.parse import urlparse
import tempfile
import time
import requests

detector_address = 'http://localhost:9191/api/v1/detect'

class RemoteImage:
    def __init__(self, url):        
        self.url = url
        self.path = None
        pr = urlparse(self.url)
        suffix = os.path.splitext(pr.path)[1]
        r = requests.get(url)  
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            self.path = tmp.name
            tmp.file.write(r.content)

    def __del__(self):
        if self.path:
            os.unlink(self.path)

    def download(self):
        pass

    def detect_nudity(self):
        img = Image.open(self.path)
        w, h = img.size
        if w<200 or h<200:
            # boring! maybe icon
            return ValueError('Image is too small')

        files = {'image': open(self.path,'rb')}
        r = requests.post(detector_address,files=files)
        return r.json()['an_algorithm_for_nudity_detection']
