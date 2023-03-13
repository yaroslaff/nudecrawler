# nude crawler

Nude crawler crawls all pages on telegra.ph for today and N past days for specific words, checks number of nude, non-nude images, videos (not analysed) and reports pages which looks interesting (e.g. has more then 10 nude images, or has one video)

## Install

```
pip3 install nudecrawler
```

alternatively, install right from git repo:
```
pip3 install git+https://github.com/yaroslaff/nudecrawler
```

## start adult-image-detector 
If you want nudity detection, we use optional [adult-image-detector](https://github.com/open-dating/adult-image-detector):

~~~
docker run -d -p 9191:9191 opendating/adult-image-detector
~~~

Or just add `-a` option if you do not want to filter by number of nude images.



## Launch Nude Crawler!

(I intentionally changed links, do not want to violate github policy)
~~~
$ nudecrawler sasha-grey
INTERESTING https://telegra.ph/sasha-grey-XXXXXXXX
  Nude: 0 non-nude: 0
  Total video: 1

INTERESTING https://telegra.ph/sasha-grey-XXXXX
  Nude: 9 non-nude: 6

INTERESTING https://telegra.ph/sasha-grey-XXXXX
  Nude: 9 non-nude: 6

INTERESTING https://telegra.ph/sasha-grey-XXXXX
  Nude: 6 non-nude: 3
~~~

## Working with wordlists
In simplest case (not so big wordlist), just use `-w`, like:
~~~shell
# verbose, no-filtering (report all pages), use wordlist
nudecrawler -v -a -w wordlist.txt
~~~

If you have very large wordlist, better to pre-check it with faster tool like [bulk-http-check](https://github.com/yaroslaff/bulk-http-check), it's much faster, doing simple check (we need only filter-out 200 vs 404 pages) millions of page per hour on smallest VPS server.

Convert wordlist to urllist
~~~shell
# only generate URLs 
nudecrawler -v -w wordlist.txt --urls > urls.txt
~~~
Verify it with [bulk-http-check](https://github.com/yaroslaff/bulk-http-check) and get output file with this format:
~~~
https://telegra.ph/abazhurah-02-26 OK 404
https://telegra.ph/ab-03-01 OK 200
https://telegra.ph/aaronov-02-22 OK 404
https://telegra.ph/abazhurami-02-25 OK 404
~~~

Filter it, to leave only existing pages, and strip date from it:
~~~
grep "OK 200" .local/urls-status.log | cut -f 1 -d" "| sed 's/-[0-9]\+-[0-9]\+$//g' | sort | uniq > .local/urs.txt
~~~

List (urls.txt) will look like:
~~~
https://telegra.ph/
https://telegra.ph/a
https://telegra.ph/ab
https://telegra.ph/aba
https://telegra.ph/Abakan
....
~~~
This list (~300Kb, 11k urls) created from 1.5M words russian wordlist. There are only words which had at least one page with this title for last 10 days. So it has words 'Анжелика' or 'Анфиса' (beautiful woman names), but has no words 'Абажурами' or 'Абажуродержателем').

Now you can use this file as wordlist (nudecrawler will detect it's already base URL, and will only append date to URL). 

## Example usage:
~~~
bin/nudecrawler -w urls.txt --nude 5 -d 30 -b --stats /tmp/nudecrawler-stats.txt | tee logs/urls.log
~~~
process urls from urls.txt, report page if 5+ nude images (or 1 any video, default), check from todays date to 30 days ago, unbuffer output and log it to logs/urls.log, save periodical statistics to /tmp/nudecrawler-stats.txt

## Options
~~~
usage: nudecrawler [-h] [-d DAYS] [--nude NUDE] [--video VIDEO] [-u URL] [-v] [words ...]

Telegra.ph Spider

positional arguments:
  words

options:
  -h, --help            show this help message and exit
  -d DAYS, --days DAYS
  --nude NUDE           Interesting if N nude images
  --video VIDEO         Interesting if N video
  -u URL, --url URL     process one url
  -v, --verbose         verbose
~~~