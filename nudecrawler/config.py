import toml
import argparse
import os
import sys
from dotenv import load_dotenv
from .version import __version__
from rich.pretty import pprint
from collections import ChainMap
import collections.abc

config_path = None
config = dict()

def get_config_path():

    def first_file(file_paths):
        for file_path in file_paths:
            if not file_path:
                continue
            if os.path.isfile(file_path):
                return file_path
        return None

    config_path_list = [
        os.getenv('NUDECRAWLER_CONFIG'),
        '/run/nudecrawler.toml',
        'nudecrawler.toml',
        os.path.expanduser('~/nudecrawler.toml'),
        '/etc/nudecrawler.toml',
    ]    

    def_config_path = first_file(config_path_list)
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-c', '--config', default=def_config_path)
    args, _ = parser.parse_known_args()
    return args.config


def read_config():
    global config_path

    load_dotenv()  

    config_path = get_config_path()

    try:
        assert config_path is not None
        with open(config_path, 'r') as f:
            user_config = toml.load(f)
    except AssertionError:
        print("No config files found, using default")
        user_config = dict()
    except toml.decoder.TomlDecodeError as e:
        print(f"Error in toml file {config_path}: {e}")
        sys.exit(1)

    hydrate_config(user_config)


def get_args(argv: str, methods_list: list[str], context_fields: list):

    read_config()

    parser = argparse.ArgumentParser(description=f'Nudecrawler: Telegra.ph Spider {__version__}\nhttps://github.com/yaroslaff/nudecrawler', formatter_class=argparse.RawTextHelpFormatter)

    # 
    parser.add_argument('words', nargs='*')
    parser.add_argument('--url1', metavar="URL", help='process only one url')
    parser.add_argument('--day', nargs=2, type=int, metavar=('MONTH', 'DAY'), help='Current date (default is today) example: --day 12 31')
    parser.add_argument('-c', '--config', default=config_path, help=f'Path to nudecrawler.toml, ({config_path})')
    parser.add_argument('-v', '--verbose', default=config['verbose'], action='store_true', help='verbose')
    parser.add_argument('--unbuffered', '-b', default=config["unbuffered"], action='store_true', help='Use unbuffered stdout')


    g = parser.add_argument_group('Depth')
    g.add_argument('-d', '--days', type=int, default=config['depth']['days'], help=f'check N days back ({config["depth"]["days"]})')
    g.add_argument('-f', '--fails', type=int, default=config['depth']['fails'], help=f'stop searching next pages with same words after N failures ({config["depth"]["fails"]})')


    g = parser.add_argument_group('Page filtering options')
    g.add_argument('-a', '--all', default=False, action='store_true', help='do not detect, print all found pages')
    g.add_argument('--expr', '-e', metavar='EXPR', default=config['filter']['expr'], 
                        help=f'Interesting if EXPR is True. def: { config["filter"]["expr"] }\nFields: ' + ' '.join(context_fields) )
    g.add_argument('--total', metavar='N', type=int, default=config['filter']['total'], help=f'Skip detections if less then N total images ({config["filter"]["total"]})')
    g.add_argument('--max-errors', metavar='N', type=int, default=config['filter']['max-errors'], help=f'Max allowed errors on page ({config["filter"]["max-errors"]})')
    g.add_argument('--min-content-length', metavar='N', type=int, default=config['filter']['min-content-length'], help=f'Skip page if content-length less then N (try 5000 or higher)')

    g = parser.add_argument_group('Image detection options')
    g.add_argument('--detect', metavar='METHOD', default=config["detect"]["detect"], help=f'One of {methods_list} ({config["detect"]["detect"]})')
    g.add_argument('--extensions', nargs='*', default=config['detect']['extensions'],help='interesting extensions (with dot, like .jpg)')
    g.add_argument('--minsize', type=int, default=config['detect']['minsize'],help=f'min size of image in Kb ({config["detect"]["minsize"]})')
    g.add_argument('--max-pictures', type=int, metavar='N', 
                   default=config["detect"]["max-pictures"], 
                   help=f'Detect only among first prefiltered N pictures')


    g = parser.add_argument_group('Cache')
    g.add_argument('--cache', metavar='PATH', default=config["cache"]["cache"], help=f'path to cache file (will create if missing)')
    g.add_argument('--cache-save', type=int, metavar='N', default=config["cache"]["cache-save"], help=f'Save cache after N new images ({config["cache"]["cache-save"]})')

    g = parser.add_argument_group('Externat detector')
    g.add_argument('--detect-image', metavar='SCRIPT', default=config["detector"]["detect-image"], help='explicitly use this script to detect nudity on image file')
    g.add_argument('--detect-url', metavar='SCRIPT', default=config["detector"]["detect-url"], help='explicitly use this script to detect nudity on image URL')


    g = parser.add_argument_group('Long-run options')
    g.add_argument('--log', default=config["longrun"]["log"], help='print all precious treasures to this logfile')
    # g.add_argument('--bugreport', default=False, action='store_true', help='send bugreport in case of problem (works only after agreed in github ticket)')
    g.add_argument('--workdir', default=config["longrun"]["workdir"], help=f'Use all files (log, wordlist, cache) in this dir. def: { config["longrun"]["workdir"] }')

    g.add_argument('-w', '--wordlist', help='wordlist (urllist) file')
    g.add_argument('--stats', metavar='STATS_FILE', default=config["longrun"]["stats"], help='periodical statistics file')
    g.add_argument('--resume', metavar='STATS_FILE', help='resume from STATS_FILE (other args are not needed)')
    g.add_argument('--stop', type=int, default=config["longrun"]["stop"], metavar='NUM_IMAGES', help='stop (or --refresh) after N images processed (or little after)')
    g.add_argument('--refresh', metavar=('SCRIPT', 'ARG'), nargs='+', help='run this refresh script every --stop NUM_IMAGES images')

    return parser.parse_args(argv)

def hydrate_config(user_conf: dict):
    global config
    
    def update(d, u):
        """ recursive dict update """
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    config.update(get_default_config())

    update(config, user_conf)

def get_default_config():
    
    def_config = {
        'verbose': False,
        'unbuffered': False,
        'depth': {
            'days': 10,
            'fails': 5,
        },
        'filter': {
            'all': False,
            'expr': 'nude_images > 0',
            'total': int(os.getenv('NUDE_TOTAL', '1')),
            'max-errors': 5,
            'min-content-length': None
        },
        'detect': {
            'detect': os.getenv('NUDE_DETECT','nudenetb'),
            'extensions': ['.jpeg','.jpg', '.png'],
            'minsize': 10,
            'max-pictures': None
        },
        'detector': {
            'detect-image': None,
            'detect-url': None,
        },
        'cache': {
            'cache': os.getenv('NUDE_CACHE'),
            'cache-save': 1000
        },
        'longrun': {
            'log': os.getenv('NUDE_LOG'),
            'workdir': os.getenv('NUDE_DIR', '.'),
            'wordlist': None,
            'stats': os.getenv('NUDE_STATS', '/tmp/nudecrawler-stats.txt'),
            'stop': None,
            'refresh': None
        },
        'nudenet': {
            'FEMALE_BREAST_EXPOSED': 0.5,
            'BUTTOCKS_EXPOSED': 0.5,
            'FEMALE_GENITALIA_EXPOSED': 0.5,
            'MALE_GENITALIA_EXPOSED': 0.5,
            'ANUS_EXPOSED': 0.5,
            'ignore': ['FEMALE_BREAST_COVERED', 'BELLY_EXPOSED', 'FEMALE_GENITALIA_COVERED', 
                       'FACE_FEMALE', 'FACE_MALE', 
                       'MALE_BREAST_EXPOSED', 'FEET_EXPOSED', 'BELLY_COVERED', 'BELLY_EXPOSED', 'FEET_COVERED',
                        'ARMPITS_COVERED', 'ARMPITS_EXPOSED', 'ANUS_COVERED', 'FEMALE_BREAST_COVERED', 
                        'BUTTOCKS_COVERED']



        }
    }

    return def_config
