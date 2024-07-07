from rich.pretty import pprint

import os
import requests
from urllib.parse import urlparse
import tempfile
import sys
import subprocess
import nude
from .exceptions import ProblemImage
from .verbose import printv
from .nudenet import nudenet_detect

# detector_address = 'http://localhost:9191/api/v1/detect'


class RemoteImage:
    def __init__(self, url:str, page_url: str = None):        
        self.url = url
        self.page_url = page_url
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

        self.threshold = float(os.getenv('NUDE_DETECT_THRESHOLD', '0.5'))

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

        if script == ':true':
            return True

        if script == ':false':
            return False

        if script==':nude':
            n = nude.Nude(self.path)            
            n.resize(maxheight=800, maxwidth=600)
            return n.parse().result
        
        if script==':nudenet':
            return nudenet_detect(path=self.path, page_url=self.page_url)

        rc = subprocess.run([script, self.path], env=os.environ.copy())
        if rc.returncode >= 100:
            print("FATAL ERROR")
            sys.exit(1)        
        return bool(rc.returncode)

