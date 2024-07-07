#!/usr/bin/env python3

from flask import Flask, request
from nudenet import NudeDetector
import os
import sys
import daemon
from daemon import pidfile
#import lockfile
import argparse
import signal
from PIL import UnidentifiedImageError
from rich.pretty import pprint

from ..config import read_config, get_config_path
from ..nudenet import nudenet_detect

app = Flask(__name__)

pidfile_path = '/tmp/.nudenet-server.pid'

@app.get("/ping")
def ping():
    return "ну вот pong, и что?"


@app.route("/detect", methods=["POST"])
def detect():
    path = request.json['path']
    page = request.json['page']

    try:
        verdict = nudenet_detect(path=path, page_url=page)
    except UnidentifiedImageError as e:
        print(f"Err: {page} {e}")
        result = {
            'status': 'ERROR',
            'error': str(e)
        }
        return result
    except Exception as e:
        print(f"Got uncaught exception {type(e)}: {e}")
    
    pprint(f'{page}: {verdict}')
    return dict(verdict=verdict, page=page)


def get_args():
    config_path = get_config_path()
    parser = argparse.ArgumentParser('Daemonical REST API for NudeNet')
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('-d', '--daemon', action='store_true', default=False)
    parser.add_argument('-c', '--config', default=config_path, help=f'Path to nudecrawler.toml, ({config_path})')
    parser.add_argument('--kill', action='store_true', default=False)
    parser.add_argument('--pidfile', default=pidfile_path)
    return parser.parse_args()

def main():
    global classifier
    global pidfile


    read_config()
    args = get_args()

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
    