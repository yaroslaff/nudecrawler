#!/usr/bin/env python

import argparse
import datetime
import transliterate
import nudecrawler.tgru

def process_word(word, counter=0):
    if word.startswith("https://"):
        baseurl = word
    else:
        trans_word = transliterate.translit(word, 'tgru', reversed=True)
        baseurl=f'https://telegra.ph/{trans_word}'


    baseurl = baseurl.replace(" ", "-")

    date = datetime.datetime.strptime("2024-01-01", "%Y-%m-%d")
    for d in range(0, 365):
        date += datetime.timedelta(days=1)
        for c in range(0, counter+1):
            url=f'{baseurl}-{date.month:02}-{date.day:02}'
            if c:
                url=f'{url}-{c}'
            print(url)


def get_args():
    parser = argparse.ArgumentParser(
        description="A simple argument parser",
        epilog="This is where you might put example usage"
    )

    parser.add_argument('-w', '--wordlist', help='wordlist txt file to check')
    parser.add_argument('-c', '--count', type=int, default=0, help='max value for counter (3rd number in filename)')
    parser.add_argument('WORD', nargs='*', help='words as arguments (if no --wordlist)')

    return parser.parse_args()

def main():
    args = get_args()

    if args.wordlist:
        counter = args.count
        with open(args.wordlist, 'r') as fh:
            words = [line.rstrip() for line in fh]
    else:
        words = args.WORD

    for w in words:
        process_word(w, counter=args.count)

if __name__ == '__main__':
    main()