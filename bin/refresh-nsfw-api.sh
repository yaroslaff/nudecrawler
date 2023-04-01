#!/bin/bash

IMAGE=ghcr.io/arnidan/nsfw-api:latest
NAME=nsfw-api

echo stop current container....
sudo docker stop $NAME

echo start new container....
sudo docker run --rm --name $NAME -d -p 3000:3000 $IMAGE
sleep 2

