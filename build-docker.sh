#!/bin/bash

MODE=${1:-dev}

# sudo docker build --build-arg VERSION=0.3.10 -t yaroslaff/nudecrawler:0.3.10 -f docker/Dockerfile .

VERSION=`python -c 'import nudecrawler.version; print(nudecrawler.version.version)'`
echo $MODE version: $VERSION

if [ "$MODE" == "dev" ]
then
    echo build development mode
    sudo docker build -t yaroslaff/nudecrawler:dev -f docker/DevDockerfile .
elif [ "$MODE" == "publish" ]
then
    echo publish version $VERSION
    # python3 setup.py bdist_wheel sdist
    # twine upload dist/nudecrawler*$VERSION*
    
    echo build version $VERSION
    echo === $VERSION
    sudo docker build --build-arg VERSION=${VERSION} -t yaroslaff/nudecrawler:${VERSION} -f docker/Dockerfile .

    echo === LATEST
    sudo docker build --build-arg VERSION=${VERSION} -t yaroslaff/nudecrawler:latest -f docker/Dockerfile .
else
    echo dev of publish?
fi
