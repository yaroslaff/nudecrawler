FROM python:3.9-bullseye
WORKDIR /
# RUN apt update && apt install -y less lsof curl 
# RUN apt update && \
#    apt -y install python3-pip && \
RUN   pip3 install -U pip nudenet flask python-daemon evalidate transliterate pytest nudepy python-dotenv bs4 pillow requests python-dotenv && \
      mkdir /work

      #mkdir /root/.NudeNet && \
      #wget -q https://nudecrawler.netlify.app/classifier_model.onnx -O /root/.NudeNet/classifier_model.onnx && \
ADD docker/.env /

ARG VERSION
# ADD . nudecrawler/
# RUN cd nudecrawler && ls -l && python3 setup.py bdist_wheel && pip3 install dist/nudecrawler*whl
RUN pip3 install nudecrawler==$VERSION


