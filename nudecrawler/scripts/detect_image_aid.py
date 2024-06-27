#!/usr/bin/env python

"""
    script to check via docker container 
    https://github.com/open-dating/adult-image-detector
"""

import sys
import os
import requests
from nudecrawler.exceptions import *
from nudecrawler.localimage import basic_check
from urllib.parse import urljoin

start_detector = "sudo docker run --rm --name aid -d -p 9191:9191 opendating/adult-image-detector"

def detect_nudity(path, address, threshold):
    endpoint = urljoin(address, '/api/v1/detect')

    files = {'image': open(path,'rb')}
    try:
        r = requests.post(endpoint, files=files)
        
    except requests.RequestException as e:
        print(e)
        print("maybe detector not running?")
        print(start_detector)
        print("or add -a to skip filtering")
        sys.exit(100)

    # return r.json()['an_algorithm_for_nudity_detection']
    return int(r.json()['open_nsfw_score'] > threshold)

def main():
    image_path = sys.argv[1]

    detector_address = os.getenv('DETECTOR_ADDRESS', 'http://localhost:9191/')
    detector_threshold = float(os.getenv('DETECTOR_THRESHOLD', '0.5'))
    min_w = int(os.getenv('DETECTOR_MIN_W', '0'))
    min_h = int(os.getenv('DETECTOR_MIN_H', '0'))

    try:
        basic_check(image_path, min_w, min_h)
    except NudeCrawlerException as e:
        sys.exit(0)

    c = detect_nudity(image_path, address=detector_address, threshold=detector_threshold)
    sys.exit(c)

if __name__ == '__main__':
    main()
