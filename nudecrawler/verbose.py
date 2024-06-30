import inspect
import os
import requests
import json
import base64

verbose = False
# send_bugreports = False

def get_verbose():
    return verbose

def printv(*args):
    if not verbose:
        return
    
    if False:
        frame = inspect.stack()[1]
        location = os.path.basename(frame.filename) + ':' + str(frame.lineno)
        print(f"...", f"({location})", *args)
    else:
        print(f"...", *args)

