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