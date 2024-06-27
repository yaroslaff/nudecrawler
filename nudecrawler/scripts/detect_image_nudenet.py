#!/usr/bin/env python

"""
    script to check via NudeNet
    https://github.com/notAI-tech/NudeNet
"""

import sys
import os
import requests
from nudecrawler.exceptions import *
from nudecrawler.localimage import basic_check
from urllib.parse import urljoin

# from nudenet import NudeClassifier

start_detector="detect-server-nudenet.py"

def detect_nudity(path, address, threshold):
    endpoint = urljoin(address, '/detect')
    try:
        r = requests.post(endpoint, json={'path': path, 'page': os.getenv('NUDECRAWLER_PAGE_URL')})
        r.raise_for_status()

    except requests.RequestException as e:
        print(e)
        print("maybe detector not running?")
        print(start_detector)
        print("or add -a to skip filtering")
        sys.exit(100)
    
    if r.json()['status']=='ERROR':
        print(f"Error for page {os.getenv('NUDECRAWLER_PAGE_URL','')}: {r.json()['error']}")
        return 0

    return int(r.json()['unsafe'] > threshold)
    
def main():
    image_path = sys.argv[1]

    detector_address = os.getenv('DETECTOR_ADDRESS', 'http://localhost:5000/')
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
