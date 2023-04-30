# 0.2.4 (2023-04-03)
- Count number of new (not found in cache) total/nude/nonnude images
- init stats keys if loaded from stats file of older version
- urls.txt converted to lowercase (and about duplicates are removed)
- unified verbose (-v) print (vprint)

# 0.3.3 (2023-04-03)
- evalidate support 
- persistent cache
- new built-in fake detectors true and false
- very basic pytest test added
- fixed bug in transliteration RU->EN
- detect-server-nudenet.py can work as daemon now
- autostart(/stop) nudenet server
- dotenv

# 0.3.4
- --bugreport

# 0.3.6
- Dockerfile
- --workdir option
- --max-pictures
- built-in optional nudenetb detector (if nudenet is installed)

# 0.3.7
- NUDE_TOTAL

# 0.3.8
- typo fixed, README

# 0.3.11
- fixed --workdir / --resume in docker image

# 0.3.13
- Catch errors (and not crash) with broken images
- Load nudenet classifier only when needed

# 0.3.14
- suppress logging from nudenetb

# 0.3.16
- conditionally print number of new images

# 0.3.17
- Better cache saving: save cache to tmp file and rename, nice error if json damaged, --cache-save option

# 0.3.19
- JSONL support for output log
