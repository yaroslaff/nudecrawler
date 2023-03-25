# nude crawler

Nude crawler crawls all pages on telegra.ph for today and N past days for specific words, checks number of nude, non-nude images, videos (not analysed) and reports pages which looks interesting (e.g. has more then 10 nude images, or has one video)

## Ineffective intriguing warning
No matter how old you are, no matter how tolerant you are, no matter what your sexual orientation is, no matter what your favorite perversion is, no matter how big your sexual horizons are, with NudeCrawler you will find a lot of things that **you will NOT like**.

I wrote this warning because I have seen some shit. LITERALLY.

Please use it only for legal and ethical purposes. And it's 18+ surely. 

## Install

```
pip3 install nudecrawler
```

alternatively, install right from git repo:
```
pip3 install git+https://github.com/yaroslaff/nudecrawler
```


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

## Working with different nudity detectors

NudeCrawler can work with different nudity detectors and very easy to extend. Option `-a`/`--all` will disable detection totally, and it will report all pages.

Bult-in filter `:nude` based on [nude.py](https://github.com/hhatto/nude.py), (python port of [nude.js](https://github.com/pa7/nude.js)) is mostly good and used by default (and does not needs to install many dependecties as with keras/tensorflow detectors, which better to use as Docker images), but it's slower

There are two options to connect third-party filters, `--detect-image SCRIPT` and `--detect-url SCRIPT`, first one will call script and pass it filename of downloaded image to analyse, and second one will call script and pass it URL of image to analyse. Script should return with either 0 return code (image is SFW) or 1 (image is NSFW). Mnemonic: return code is number of *interesting* images. 

if you will use `/bin/true` as script, it will detect all images as nude, and `/bin/false` will detect all images as non-nude.

### detector: adult-image-detector 
To use [adult-image-detector](https://github.com/open-dating/adult-image-detector):
~~~
docker run -d -p 9191:9191 opendating/adult-image-detector

# or limit to 4G RAM
sudo docker run -d -p 9191:9191 --memory=4G opendating/adult-image-detector

# or 
sudo docker run --rm -d -p 9191:9191 --name aid --memory=1G opendating/adult-image-detector
~~~

And use option `--detect-image PATH-TO/detect-image-aid.py` (usually: `/usr/local/bin/aid.py`)

adult-image-detector works good and fast for me, but has memory leaking so needs more and more RAM. It's good for short-time run

### detector: nsfw_api (recommended)

To use [nsfw_api](https://github.com/arnidan/nsfw-api):

Start:
~~~
sudo docker run --rm --name nsfw-api -d -p 3000:3000 ghcr.io/arnidan/nsfw-api:latest
~~~

Use option `--detect-image PATH_TO/detect-url-nsfw-api.py`

This detector understands DETECTOR_VERBOSE, and special threshold for each of NSFW classes (porn, sexy, hentai),
also, DETECTOR_THRESHOLD sets default threshold for all classes.
~~~
DETECTOR_VERBOSE=1 DETECTOR_THRESHOLD_HENTAI=0.9 bin/detect-image-nsfw-api.py /tmp/sketch-girl.jpg ; echo $?
Safe /tmp/sketch-girl.jpg: {'hentai': 0.57, 'drawing': 0.4, 'porn': 0.02, 'neutral': 0.01, 'sexy': 0.0}
0
~~~

### detector: NudeNet

#### Installing NudeNet (little trick needed)
Using NudeNet does not requires docker, but you need to install `pip3 install -U nudenet`. Also, NudeNet requires model in file `~/.NudeNet/classifier_model.onnx`, if file is missing, NudeNet *tries* to download file from https://github.com/notAI-tech/NudeNet/releases/download/v0/classifier_model.onnx but there is problem, github may display warning page instead of real .onnx file, so this page is downloaded (which is certainly wrong).

Workaround is simple - after you will install NudeNet download model *manually* (no wget!) and place it to `~/.NudeNet/`

#### Using NudeNet with NudeCrawler
[NudeNet](https://github.com/notAI-tech/NudeNet) filtering is implemented as client-server. Start server (PATH_TO/detect-server-nudenet.py) on other terminal (or screen/tmux) and add option `--detect-image PATH_TO/detect-image-nudenet.py` to NudeCrawler.

### Writing your own detector
If you want to write your own detector, explore current detector scripts as example, buy main rules:
- Image URL or PATH passed as argv[1]
- Return 0 if image is safe and boring, return 1 if image is interesting
- Return 0 if there are any technical problems (timeout or 404)
- Additioncal configuration could be specified via environment, NudeCrawler will pass environment to your script
- NudeCrawler also sets env variables `NUDECRAWLER_PAGE_URL` and `NUDECRAWLER_IMAGE_URL`


### Prefiltering
To speed-up processing, nudecrawler uses pre-filtering, HTTP HEAD request is performed for any image, and further processing is performed only if images passes basic check:
- Image URL must return status 200
- If server responds with Content-Length in response headers (telegra.ph uses Content-Length), it must be more then `--minsize` (minsize specified in Kb, and default value is 10Kb). This saves us from downloading/filtering icons.


### Benchmarking/test
Tested on same page, different technologies (default thresholds) gives different results:

| filtering technology           | time   | results                                       |
|---                             |---     |---                                            |
|:nude (bilt-in)                 | 3m 16s | total: 22 (need: 1) nude: 15 (1) video: 0 (1) |
|detect-image-nsfw_api (docker)  | 31s    | total: 22 (need: 1) nude: 20 (1) video: 0 (1) |
|detect-image-detector (docker)  | 37s    | total: 22 (need: 1) nude: 10 (1) video: 0 (1) |
|detect-image-nudenet  (scripts) | 32s    | total: 22 (need: 1) nude: 20 (1) video: 0 (1) |




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
This list (~300Kb, 11k urls) created from 1.5M words russian wordlist. There are only words which had at least one page with this title for last 10 days. So it has words 'Анжелика' or 'Анфиса' (beautiful woman names), but has no words 'Абажурами' or 'Абажуродержателем' (Because there are no pages with these titles on telegra.ph).

Now you can use this file as wordlist (nudecrawler will detect it's already base URL, and will only append date to URL). 

## Example usage:
~~~
bin/nudecrawler -w urls.txt --nude 5 -d 30 -f 5 --stats .local/mystats.json  --log .local/nudecrawler.log 
~~~
process urls from urls.txt, report page if 5+ nude images (or 1 any video, default), nudity must be over 0.5 threshold, check from todays date to 30 days ago, append all found pages to .local/nudecrawler.log, save periodical statistics to .local/mystats.json

If crawler will see page `Sasha-Grey-01-23-100`, but `Sasha-Grey-01-23-101` is 404 Not Found, it will try `-102` and so on. It will stop only if 5 (-f) pages in a row will fail. 

If you will stop nude crawler for some reason, you can resume it. Repeat full command (peek it from stats file) and append `--resume`.

## Options
~~~
usage: nudecrawler [-h] [-d DAYS] [--nude NUDE] [--video VIDEO] [-u URL] [-a] [-f FAILS]
                   [-t THRESHOLD] [--day MONTH DAY] [-v] [--unbuffered] [--urls] [--log LOG]
                   [-w WORDLIST] [--stats STATS] [--resume]
                   [words ...]

Telegra.ph Spider

positional arguments:
  words

optional arguments:
  -h, --help            show this help message and exit
  -d DAYS, --days DAYS
  --nude NUDE           Interesting if N nude images
  --video VIDEO         Interesting if N video
  -u URL, --url URL     process one url
  -a, --all             do not detect, print all found pages
  -f FAILS, --fails FAILS
                        stop searching next pages with same words after N failures
  -t THRESHOLD, --threshold THRESHOLD
                        nudity threshold (0..1), 0 will match almost everything
  --day MONTH DAY       Current date (default is today) example: --day 12 31

Output options:
  -v, --verbose         verbose
  --unbuffered, -b      Use unbuffered stdout
  --urls                Do not check, just generate and print URLs
  --log LOG             print all precious treasures to this logfile

list-related options:
  -w WORDLIST, --wordlist WORDLIST
                        wordlist (urllist) file
  --stats STATS         periodical statistics file
  --resume              skip all words before WORD in list, resume starting from it
~~~