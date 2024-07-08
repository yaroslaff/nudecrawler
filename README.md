# nude crawler

Nude crawler crawls all pages on telegra.ph for today and N past days for specific words, checks number of nude, non-nude images, videos (not analysed) and reports pages which looks interesting (e.g. has more then 10 nude images, or has one video)

## Ineffective intriguing warning
No matter how old you are, no matter how tolerant you are, no matter what your sexual orientation is, no matter what your favorite perversion is, no matter how big your sexual horizons are, with NudeCrawler you will find a lot of things that **you will NOT like**.

I wrote this warning because I have seen some shit. LITERALLY.

Please use it only for legal and ethical purposes. And it's 18+ surely. 

## Install

Recommended (and most secure) way is using docker:
```
mkdir /tmp/run
sudo docker run --rm -v /tmp/run:/work yaroslaff/nudecrawler nudecrawler -a Eva "Sasha Grey" "Belle Delphine" Amouranth
```

See below how to refine your searching and filtering.

### Alternative install
```
pipx install nudecrawler
```
or, install right from git repo:
```
pipx install git+https://github.com/yaroslaff/nudecrawler
```

on old Linux without pipx, you may use pip3 (and better to install in virtualenv).

## Launch Nude Crawler!

(I intentionally changed links in results, do not want to violate github policy)
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

By default, built-in [NudeNet](https://github.com/notAI-tech/NudeNet) detection (`--detect nudenetb`) is used (but nudecrawler has open architecture, natively supports few other detectors and you can easily connect it to any other detectors).

For very impatient, add `-a` (skip nudity detection, print all found pages) and `-v` (verbose) options to skip detections.

## Config file
Most of nudecrawler options could be configured from config file [nudecrawler.toml](https://raw.githubusercontent.com/yaroslaff/nudecrawler/master/nudecrawler.toml). Nudecrawler looks for config file in following locations (first found file is used):
-  `NUDECRAWLER_CONFIG` environment variable or `-c` / `--config` option
-  `/run/nudecrawler.toml` (This used when working inside docker contaner and host directory mounted as /run/)
-  `nudecrawler.toml` in current working directory
-  `~/nudecrawler.toml`
-  `/etc/nudecrawler.toml`

options given in command line has higher priority.


## Advanced usage

### How to get only most interesting results
Nudecrawler uses [evalidate](https://github.com/yaroslaff/evalidate) to filter results with python expression (`--expr`). With `-h` help will list all avaliable variables, like: `total_images`, `nude_images`, `nonnude_images`, `new_nude_images`, `new_nonnude_images`, `new_total_images`, `total_video`. `new_` variables are about new images (not found in cache). e.g. `--expr 'total_images>20 and new_nude_images>5'` will print only pages with more then 20 images and 5 nude images (not found in cache). This is good method to skip pages with duplicated content.

Default value: `nude_images > 0`. 

Use `-a`/`--all` to get some results ASAP (but later you may want to make some filtering)

Consider using `--days`, `--total` to narrow/wider search.


See also "How to use JSON log files".

### How to search faster

#### How to search faster: use cache 
Nudecrawler use very simple cache in JSON format (with two mappings: image url to SHA1 hash of image, and hash to verdict). Sometimes this can speed-up searching greatly, because often some pages are very similar to each other and we can reuse verdict from cache, not doing heavy AI analysis of image and sometimes not even downloading image.

config section
~~~toml
[cache]
# Path to cache file
cache = "/tmp/nccache.json"
cache-save = 1
~~~

`cache-save` is how often we should save in-memory cache to file. With 1 it will be saved after each new file is added to cache. Set it to higher value like 100 or 1000 for very long runs, because saving big cache is slow.



#### How to search faster: use prefiltering for images
To speed-up processing, nudecrawler uses pre-filtering, HTTP HEAD request is performed for any image, and further processing is performed only if images passes basic check:
- Image URL must return status 200
- If server responds with Content-Length in response headers (telegra.ph uses Content-Length), it must be more then `--minsize` (minsize specified in Kb, and default value is 10Kb). This saves us from downloading/filtering icons or other very small images.


#### How to search faster: discard useless pages before analysis

Use argument `--total N` (section `[filter]`, option `total`) to analyse only pages which has more then N images (images discarded on pre-filtered stage do not count). So, if total is 20, images which has less then 20 big images will be discarded quickly.

`--max-pictures` (section `[filter]`, option `max-pictures`) will analyse only first N prefiltered images. So, if page has 1000 images, but `max-pictures` is 10, only first 10 images will be analysed. (and variables like `nude_images` will never be higher then N)

`--max-errors` (section `[filter]`, option `max-errors`) limits number of errors on page (like broken image links), if N errors happened, page is discarded and not processed further.

`--min-content-length` (section `[filter]`, option `max-content-length`) skips pages with too small content-length.


### How to search very fast (without detection)
If you want just to find existing pages in telegra.ph (and do not want to detect nudity on images there or any other filtering) you can use `nudecrawler-makeurls` utility in combination with [bulk-http-check](https://github.com/yaroslaff/bulk-http-check)

~~~
 $ time nudecrawler-makeurls "sasha grey" -c 10 | bulk-http-check -n 100 |grep "200$"
https://telegra.ph/sasha-grey-01-12 OK 200
https://telegra.ph/sasha-grey-01-14 OK 200
...
https://telegra.ph/sasha-grey-12-12 OK 200

real	0m5.089s
user	0m1.079s
sys	0m0.444s
~~~

5 seconds to find all (61) telegra.ph pages with title "Sasha Grey".

### Long-time run

#### Stop/Resume
When working with worklists an --stats file, current status is periodically saved to this file. If you need to resume it, just use command `nudecrawler --resume PATH/TO/stats.json`

#### Memory leaking in containers (if using detectors in docker containers)
You may check container memory usage with `sudo docker stats` or `sudo docker stats --no-stream`. Often containers consume more and more memory with time, leading to out-of-memory in the end. To prevent this problem use combination of `--stop` and `--refresh` like `--stop 1000 --refresh refresh-nsfw-api.sh` this will call refresh script every 1000 images. Refresh script should stop current container and start it again. See source of [refresh-nsfw-api.sh](https://raw.githubusercontent.com/yaroslaff/nudecrawler/master/run/refresh-nsfw-api.sh) for example, it's very simple. This shell script is not installed when you install nudecrawler python package.

### Benchmarking/test
Tested on same page, different technologies (default thresholds) gives different results.
Page A: *belle delphine from 16th Jan* (64 lite sexy images, mostly underwear, nude breast on few)
Page B: *sasha grey* from 18 Apr (16 images, 12 clearly nsfw, 4 are clearly safe )

| filtering technology           | A time | A nudes | B time | B nudes                            |
|---                             |---     | --      |---     |---                                 | 
|:nude (bilt-in)                 | 127s   | 63      | 34s    | 14 (false positives/negatives)     |
|detect-image-nsfw_api (docker)  | 90s    | 49      | 23s    | 12                                 |
|detect-image-aid (docker)       | 124s   | 10      | 28s    | 6 (false negatives)                |
|detect-image-nudenet  (scripts) | 90s    | 57      | 24s    | 12                                 |


### Working with wordlists
While you can run nudecrawler to search few words like `nudecrawler "sasha grey" "Belle Delphine" Amouranth`, you may want to run it for long time with very long wordlist from file. 

In simplest case (not so big wordlist), just use `-w`, like:
~~~shell
# verbose, no-filtering (report all pages), use wordlist
nudecrawler -v -a -w wordlist.txt
~~~

If you have very large wordlist, better to pre-check it with faster tool like [bulk-http-check](https://github.com/yaroslaff/bulk-http-check), it's much faster, doing simple check (we need only filter-out 200 vs 404 pages) millions of page per hour on smallest VPS server.

Convert wordlist to urllist
~~~shell
# only generate URLs 
nudecrawler-makeurls -w wordlist.txt > urls.txt
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


### How to use JSON log files
If `--log` filename ends with `.json` or `.jsonl`, nudecrawler will save log in JSONL format (each line is JSON for a page). Example:

~~~
{"status": "INTERESTING", "url": "https://telegra.ph/Masha-NN-NN-N", "total_images": 29, "nude_images": 17, "new_nude_images": 17, "nonnude_images": 12, "new_nonnude_images": 12, "total_video": 0}
{"status": "INTERESTING", "url": "https://telegra.ph/Masha-NN-NN-N", "total_images": 3, "nude_images": 3, "new_nude_images": 3, "nonnude_images": 0, "new_nonnude_images": 0, "total_video": 0}
~~~

You can save almost all pages and then filter it with jq (get only interesting records, only interesting fields):
~~~
jq 'select(.nude_images>1 and .total_images>1) | {"url": .url, "total": .total_images}' < /tmp/n.json
~~~

### Working with different nudity detectors

NudeCrawler can work with different nudity detectors and very easy to extend. Option `-a`/`--all` will disable detection totally, and it will report all pages.

Bult-in filter `:nude` based on [nude.py](https://github.com/hhatto/nude.py), (python port of [nude.js](https://github.com/pa7/nude.js)) is mostly good and used by default (and does not needs to install many dependecties as with keras/tensorflow detectors, which better to use as Docker images), but it's slower

There are two options to connect user filters, `--detect-image SCRIPT` and `--detect-url SCRIPT`, first one will call script and pass it filename of downloaded image to analyse, and second one will call script and pass it URL of image to analyse. Script should return with either 0 return code (image is SFW) or 1 (image is NSFW). Mnemonic: return code is number of *interesting* images. 

if you will use `/bin/true` as script, it will detect all images as nude, and `/bin/false` will detect all images as non-nude.

Scripts are usually installed to /usr/local/bin and if it's in $PATH, you do not need to specify full path to script, nudecrawler will find it in $PATH.



#### detector: nsfw_api (recommended)

To use [nsfw_api](https://github.com/arnidan/nsfw-api):

Start:
~~~
sudo docker run --rm --name nsfw-api -d -p 3000:3000 ghcr.io/arnidan/nsfw-api:latest
~~~

Use option `--detect nsfwapi`

This detector understands DETECTOR_VERBOSE, and special threshold for each of NSFW classes (porn, sexy, hentai),
also, DETECTOR_THRESHOLD sets default threshold for all classes.
~~~
DETECTOR_VERBOSE=1 DETECTOR_THRESHOLD_HENTAI=0.9 bin/detect-image-nsfw-api.py /tmp/sketch-girl.jpg ; echo $?
Safe /tmp/sketch-girl.jpg: {'hentai': 0.57, 'drawing': 0.4, 'porn': 0.02, 'neutral': 0.01, 'sexy': 0.0}
0
~~~

#### detector: adult-image-detector 
To use [adult-image-detector](https://github.com/open-dating/adult-image-detector):
~~~
sudo docker run --rm -d -p 9191:9191 --name aid --memory=1G opendating/adult-image-detector
~~~

And use option `--detect aid`

adult-image-detector works good and fast for me, but has memory leaking so needs more and more RAM. It's good for short-time run

#### detector: NudeNet

##### Installing NudeNet (little trick needed)
Using NudeNet does not requires docker, but you need to install `pip3 install -U flask nudenet python-daemon` (consider using virtualenv, because nudenet has many dependencies). Also, NudeNet requires model in file `~/.NudeNet/classifier_model.onnx`, if file is missing, NudeNet (unsuccessfully) *tries* to download file from https://github.com/notAI-tech/NudeNet/releases/download/v0/classifier_model.onnx but there is problem, github may display warning page instead of real .onnx file, so this page is downloaded (which is certainly wrong).

Right way workaround is simple - after you will install NudeNet download model *manually* (no wget!) and place it to `~/.NudeNet/`

Or you can download from my temporary site: `wget -O ~/.NudeNet/classifier_model.onnx https://nudecrawler.netlify.app/classifier_model.onnx` (But I cannot promise it will be there forever) and put it to ~/.NudeNet .


##### Using NudeNet with NudeCrawler
[NudeNet](https://github.com/notAI-tech/NudeNet) filtering is implemented as client-server. Start server (PATH_TO/detect-server-nudenet.py) on other terminal (or screen/tmux) and add option `--detect nudenet` to NudeCrawler.

#### Writing your own detector
If you want to write your own detector, explore current detector scripts as example, but here is main rules:
- Image URL or PATH passed as argv[1]
- Return 0 if image is safe and boring, return 1 if image is interesting
- Return 0 if there are any technical problems (timeout or 404)
- Additional configuration could be specified via environment, NudeCrawler will pass environment to your script
- NudeCrawler also sets env variables `NUDECRAWLER_PAGE_URL` and `NUDECRAWLER_IMAGE_URL`

### Building docker container
Repository includes Dockerfile. Use `sudo docker build --build-arg VERSION=0.3.10 -t yaroslaff/nudecrawler:0.3.10 -f docker/Dockerfile .` to build it.

Running docker container (example):
~~~
mkdir /tmp/run
sudo docker run -v /tmp/run:/work yaroslaff/nudecrawler nudecrawler -a Eva "Sasha Grey" "Belle Delphine" Amouranth
~~~

If you specify files for docker (like `-w`, `--stats`, `--resume`, `--log`, `--cache`) path will be modified starting from /work. e.g. `-w urls.txt` will be `-w /work/urls.txt` which is /tmp/run/urls.txt on host.


