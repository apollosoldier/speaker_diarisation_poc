FROM python:3.6

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN apt-get update
RUN apt-get install vim -y
RUN apt-get install youtube-dl -y

COPY src /src

WORKDIR src

CMD ./bootstrap.sh
