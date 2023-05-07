# docker build -t codeaster-seq . 


FROM aethereng/codeaster-seq:latest

USER root

RUN apt update
RUN apt install -y python3-pip
RUN pip3 install requests

RUN apt-get update 
RUN apt-get -y upgrade
RUN apt update
RUN apt -y upgrade

USER aster

