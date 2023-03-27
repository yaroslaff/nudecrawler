#!/usr/bin/env python

"""
    script to check via docker container 
    https://github.com/arnidan/nsfw-api

    manual curl test: curl -X POST http://localhost:3000/classify -F image=@/tmp/eropicture.jpg

"""


import sys
import json
import os
import requests
from nudecrawler.exceptions import *
from nudecrawler.localimage import basic_check
from urllib.parse import urljoin

#start_detector = "sudo docker run --rm --name nsfw-api -d -p 127.0.0.1:5000:5000/tcp --env PORT=5000 eugencepoi/nsfw_api:latest"
start_detector = "sudo docker run --rm --name nsfw-api -d -p 3000:3000 ghcr.io/arnidan/nsfw-api:latest"

timeout = 10

def detect_image(path, address, thresholds, verbose=False):

    req_url = urljoin(address,'/classify')

    try:
        files = {
            'image': open(path, 'rb')
        }
        r = requests.post(req_url, files=files)
        if r.status_code == 500:
            if verbose:                
                print(r.text)
            return  0            

        if r.status_code != 200:
            print(os.getenv('NUDECRAWLER_PAGE_URL'))
            print(os.getenv('NUDECRAWLER_IMAGE_URL'))
            print(r.text)
            print(r.json())

    except requests.Timeout as e:
        # timeout: not interesting image
        print("TIMEOUT")
        sys.exit(0)
    except requests.RequestException as e:
        print(e)
        print("maybe detector not running?")
        print(start_detector)
        print("or add -a to skip filtering")
        sys.exit(100)

    results = r.json()
    rround = {key : round(results[key], 2) for key in results}


    for cls in thresholds:
        if results[cls] > thresholds[cls]:
            if verbose:
                print(f"Nude {path} {cls}: {results[cls]:.2f} > {thresholds[cls]}")
            return 1
    
    if verbose:
        print(f"Safe {path}: {rround}")
    return 0



    # return int(r.json()['neutral'] < threshold)

def main():
    image_path = sys.argv[1]

    thresholds=dict()

    detector_address = os.getenv('DETECTOR_ADDRESS', 'http://localhost:3000/')
    detector_threshold_str = os.getenv('DETECTOR_THRESHOLD', '0.5')
    verbose = bool(os.getenv('DETECTOR_VERBOSE', ""))

    for cls in ['hentai', 'porn', 'sexy']:
        thresholds[cls] = float(os.getenv(f'DETECTOR_THRESHOLD_{cls.upper()}', detector_threshold_str))

    c = detect_image(image_path, address=detector_address, thresholds=thresholds, verbose=verbose)
    sys.exit(c)

if __name__ == '__main__':
    main()
