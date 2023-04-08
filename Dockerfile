FROM python:3.9-bullseye
WORKDIR /
# RUN apt update && \
#    apt -y install python3-pip && \
RUN   pip3 install nudecrawler[nudenet] && \
      mkdir /root/.NudeNet && \
      wget -q https://nudecrawler.netlify.app/classifier_model.onnx -O /root/.NudeNet/classifier_model.onnx && \
      mkdir /work
      
CMD /usr/local/bin/detect-server-nudenet.py 


