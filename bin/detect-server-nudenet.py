#!/usr/bin/env python3

from flask import Flask, request
from nudenet import NudeClassifier
import os
import sys
import daemon
import argparse
from PIL import UnidentifiedImageError


classifier = NudeClassifier()

app = Flask(__name__)

@app.route("/detect", methods=["POST"])
def detect():
    path = request.json['path']
    page = request.json['page']
    
    print("....", page)
    try:
        r = classifier.classify(path)
    except UnidentifiedImageError as e:
        print(f"Err: {page} {e}")
        result = {
            'status': 'ERROR',
            'error': str(e)
        }
        return result
    except Exception as e:
        print(f"Got uncaught exception {type(e)}: {e}")
    

    # sometimes no exception, but empty response, e.g. when mp4 instead of image
    if not r:
        print(f"Err: {page} empty reply")
        result = {
            'status': 'ERROR',
            'error': "empty reply from classifier"
        }
        return result
    
    
    if r[path]['unsafe'] > 0.5:
        verdict="UNSAFE"
    else:
        verdict="safe"

    r[path]['status'] = 'OK'
    print(f'{verdict} ({r[path]["unsafe"]:.2f}) {page}')
    return r[path]


def get_args():
    parser = argparse.ArgumentParser('Daemonical REST API for NudeNet')
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("-d", '--daemon', action='store_true', default=False)
    return parser.parse_args()

def sanity_check():
    def print_help(msg):
        print(f"{msg}Download original file from https://nudecrawler.netlify.app/classifier_model.onnx\n" \
              "Or from https://github.com/notAI-tech/NudeNet", file=sys.stderr)
        
    min_sane_size = 10*1024*1024
    path = os.path.expanduser('~/.NudeNet/classifier_model.onnx')

    if not os.path.exists(path):
        print_help(f"Missing {path}\n", file=sys.stderr)
        return False

    sz = os.stat(path).st_size
    
    # check if size is OK. Normally its 80M, we check if it's at least 10M
    if sz <= min_sane_size:
        print_help(f"Too small file ({sz}) {path}\n")
        return False
    
    return True


def main():
    args = get_args()
    if not sanity_check():
        sys.exit(1)
    if args.daemon:
        with daemon.DaemonContext():
            app.run(port=args.port)
    else:
        app.run(port=args.port)    

if __name__ == '__main__':
    main()
    