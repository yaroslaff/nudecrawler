#!/bin/bash

echo $1
MODE=${1:-dev}

echo mode: $MODE

# sudo docker build --build-arg VERSION=0.3.10 -t yaroslaff/nudecrawler:0.3.10 -f docker/Dockerfile .

if [ "$MODE" == "dev" ]
then
    echo build development mode
    sudo docker build -t yaroslaff/nudecrawler:dev -f docker/DevDockerfile .
fi
