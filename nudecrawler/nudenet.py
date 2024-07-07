from rich.pretty import pprint
from nudenet import NudeDetector
import onnxruntime
from PIL import Image, UnidentifiedImageError

from .config import config
from .verbose import printv

nudenet_detector = None

try:       
    nudenet_detector = NudeDetector()
except (ModuleNotFoundError, onnxruntime.capi.onnxruntime_pybind11_state.InvalidProtobuf):
    print("Unexpected problem while loading NudeNet")
    nudenet_detector = None

def nudenet_detect(path, page_url):

    nnconf = config['nudenet']

    try:
        dlist = nudenet_detector.detect(path)
    except UnidentifiedImageError as e:
        print(f"Err: {page_url} {e}")
        result = {
            'status': 'ERROR',
            'error': str(e)
        }
        return False
    except Exception as e:
        print(f"Got uncaught exception {type(e)}: {e}")
    
    # sometimes no exception, but empty response, e.g. when mp4 instead of image
    if not dlist:
        printv(f"Err: {page_url} empty reply")
        return False

    for detection in dlist:

        if detection['class'] in nnconf['ignore']:
            # print("ignore", detection['class'])
            continue
        
        try:
            threshold = nnconf[detection['class']]
        except KeyError:
            print(f"No config for nudenet class {detection['class']}")
        
        if detection['score'] >= threshold:
            printv(f"{page_url} detected by class {detection['class']} {detection['score']:.2f} > {threshold}")
            return True
            
    return False

