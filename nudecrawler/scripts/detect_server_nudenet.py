#!/usr/bin/env python3

from flask import Flask, request
from nudenet import NudeClassifier
import os
import sys
import daemon
from daemon import pidfile
#import lockfile
import argparse
import signal
from PIL import UnidentifiedImageError


classifier = None

app = Flask(__name__)

pidfile_path = '/tmp/.nudenet-server.pid'

@app.get("/ping")
def ping():
    return "ну вот pong, и что?"


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
    parser.add_argument('--kill', action='store_true', default=False)
    parser.add_argument('--pidfile', default=pidfile_path)
    return parser.parse_args()

def sanity_check():
    def print_help(msg):
        print(f"{msg}Download original file from https://nudecrawler.netlify.app/classifier_model.onnx\n" \
              "Or from https://github.com/notAI-tech/NudeNet", file=sys.stderr)
        
    min_sane_size = 10*1024*1024
    path = os.path.expanduser('~/.NudeNet/classifier_model.onnx')

    if not os.path.exists(path):
        print_help(f"Missing {path}\n")
        return False

    sz = os.stat(path).st_size
    
    # check if size is OK. Normally its 80M, we check if it's at least 10M
    if sz <= min_sane_size:
        print_help(f"Too small file ({sz}) {path}\n")
        return False
    
    return True


def main():
    global classifier
    global pidfile
    args = get_args()
    if not sanity_check():
        sys.exit(1)
    
    print("load classified")
    classifier = NudeClassifier()

    if args.kill:
        try:
            with open(pidfile_path) as fh:
                pid = int(fh.read())
                print("Killing nudenet server with pid", pid)
                os.kill(pid, signal.SIGINT)
            os.unlink(pidfile_path)
        except FileNotFoundError:
            print("no pidfile", pidfile_path, "not doing anything")
        sys.exit(0)

    if args.daemon:
        print("work as daemon...")
        with daemon.DaemonContext(
            # pidfile=lockfile.FileLock(args.pidfile)
            pidfile=pidfile.TimeoutPIDLockFile(pidfile_path)
            ):
            # pid = os.getpid()
            # with open(pidfile, "w+") as fh:
            #    print(pid, file=fh)
            print("daemon app.run")
            app.run(port=args.port)
            print("after app.run")
    else:
        app.run(port=args.port) 
    
    print("done.")   

if __name__ == '__main__':
    main()
    