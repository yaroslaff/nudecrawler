import PIL
from PIL import Image, UnidentifiedImageError
from pprint import pprint

import os
from urllib.parse import urlparse
import tempfile
import sys
import onnxruntime
import subprocess
# import nude
from .exceptions import ProblemImage
from .verbose import printv

# detector_address = 'http://localhost:9191/api/v1/detect'

nudenet_detector = None

def _load():
    global nudenet_classifier
    try:
        from nudenet import NudeDetector
        print("Loading nudenet classifier....")
        nudenet_detector = NudeDetector()
    except (ModuleNotFoundError, onnxruntime.capi.onnxruntime_pybind11_state.InvalidProtobuf):
        nudenet_detector = None



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
            if nudenet_detector is None:
                print("built-in nudenet detector selected, but nudenet is not installed or model not loaded")
                sys.exit(1)
            return self.nudenet_detect()

        rc = subprocess.run([script, self.path], env=os.environ.copy())
        if rc.returncode >= 100:
            print("FATAL ERROR")
            sys.exit(1)        
        return bool(rc.returncode)

    def nudenet_detect(self):

        print("NUDENET DETECT")

        try:
            r = nudenet_detector.detect(self.path)
        except UnidentifiedImageError as e:
            print(f"Err: {self.url} {e}")
            result = {
                'status': 'ERROR',
                'error': str(e)
            }
            return False
        except Exception as e:
            print(f"Got uncaught exception {type(e)}: {e}")
        
        # sometimes no exception, but empty response, e.g. when mp4 instead of image
        if not r:
            printv(f"Err: {self.url} empty reply")
            return False

        pprint(r)

        if r[self.path]['unsafe'] > self.threshold:
            return True
        
        return False

