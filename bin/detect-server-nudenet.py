#!/usr/bin/env python3

from flask import Flask, request
from nudenet import NudeClassifier
import os
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

if __name__ == '__main__':
    app.run(port=5000)