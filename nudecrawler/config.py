import toml
import argparse
import os
from dotenv import load_dotenv
from .version import __version__
from rich.pretty import pprint
from collections import ChainMap
import collections.abc

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
        'nudecrawler.toml',
        '~/nudecrawler.toml',
        '/etc/nudecrawler.toml'
    ]    

    def_config_path = first_file(config_path_list)
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-c', '--config', default=def_config_path)
    args, _ = parser.parse_known_args()
    return args.config


def get_args(argv: str, methods_list: list[str], context_fields: list):

    load_dotenv()  

    config_path = get_config_path()

    try:
        with open(config_path, 'r') as f:
            config = toml.load(f)
    except FileNotFoundError:
        config = dict()

    config = hydrate_config(config)
    pprint(config)

    print(config["cache"]["cache"])

    parser = argparse.ArgumentParser(description=f'Nudecrawler: Telegra.ph Spider {__version__}\nhttps://github.com/yaroslaff/nudecrawler', formatter_class=argparse.RawTextHelpFormatter)

    # 

    
    parser.add_argument('words', nargs='*')
    parser.add_argument('--url1', metavar="URL", help='process only one url')
    parser.add_argument('--day', nargs=2, type=int, metavar=('MONTH', 'DAY'), help='Current date (default is today) example: --day 12 31')
    parser.add_argument('-c', '--config', default=config_path, help=f'Path to nudecrawler.toml, ({config_path})')
    parser.add_argument('-v', '--verbose', default=["verbose"], action='store_true', help='verbose')
    parser.add_argument('--unbuffered', '-b', default=config["unbuffered"], action='store_true', help='Use unbuffered stdout')


    g = parser.add_argument_group('Depth')
    g.add_argument('-d', '--days', type=int, default=config['depth']['days'], help=f'check N days back ({config["depth"]["days"]})')
    g.add_argument('-f', '--fails', type=int, default=config['depth']['fails'], help=f'stop searching next pages with same words after N failures ({config["depth"]["fails"]})')


    g = parser.add_argument_group('Page filtering options')
    g.add_argument('-a', '--all', default=False, action='store_true', help='do not detect, print all found pages')
    g.add_argument('--expr', '-e', metavar='EXPR', default=config['filter']['expr'], 
                        help=f'Interesting if EXPR is True. def: { config["filter"]["expr"] }\nFields: ' + ' '.join(context_fields) )
    g.add_argument('--total', metavar='N', type=int, default=config['filter']['total'], help=f'Skip detections if less then N total images ({config["filter"]["total"]})')
    g.add_argument('--max-errors', metavar='N', type=int, default=config['filter']['max_errors'], help=f'Max allowed errors on page ({config["filter"]["max_errors"]})')
    g.add_argument('--min-content-length', metavar='N', type=int, default=config['filter']['min-content-length'], help=f'Skip page if content-length less then N (try 5000 or higher)')

    g = parser.add_argument_group('Image detection options')
    g.add_argument('--detect', metavar='METHOD', default=config["detect"]["detect"], help=f'One of {methods_list} ({config["detect"]["detect"]})')
    g.add_argument('--extensions', nargs='*', default=config['detect']['extensions'],help='interesting extensions (with dot, like .jpg)')
    g.add_argument('--minsize', type=int, default=config['detect']['minsize'],help=f'min size of image in Kb ({config["detect"]["minsize"]})')
    g.add_argument('--max-pictures', type=int, metavar='N', default=config["detect"]["max-pictures"], help=f'Detect only among first prefiltered N pictures')


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

def hydrate_config(conf: dict):
    
    def update(d, u):
        """ recursive dict update """
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    
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
            'max_errors': 5,
            'min-content-length': None
        },
        'detect': {
            'detect': os.getenv('NUDE_DETECT','mudepy'),
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
        }
    }

    return update(def_config, conf)
