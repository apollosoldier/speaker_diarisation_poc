FROM ubuntu:16.04

RUN apt-get update
RUN apt-get install vim python3-pip python3 -y
RUN apt-get install youtube-dl sox ffmpeg -y
RUN apt-get install python3-tk -y
RUN apt-get install cmake -y

COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN pip3 install scikit-image==0.13.1

#COPY src /src

WORKDIR src

CMD ./bootstrap.sh
