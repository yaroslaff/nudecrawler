import inspect
import os
import requests
import json
import base64

access_key = '8b53121d-d362-49de-813f-507238984803'
target='https://api.staticforms.xyz/submit'
def_subject='nudecrawler automatic bugreport'

verbose = False
send_bugreports = False

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


def bugreport(**kwargs):
    if not send_bugreports:
        return
    print("Sending bugreport....")
    data = dict()
    data['subject'] = def_subject
    data['accessKey'] = access_key

    for k,v in kwargs.items():
        if v.startswith('http://') or v.startswith('https://'):
            data['$'+k] = v.replace('.',':')
        else:
            data['$'+k] = v

    print(json.dumps(data, indent=4))

    r = requests.post(target, json=data)
    if r.status_code == 200 and r.json()['success'] == True:
        print(r.json()['message'])
