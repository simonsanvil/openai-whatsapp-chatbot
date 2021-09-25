FROM python:3.8-buster
WORKDIR /usr/src/app

RUN apt-get update 
RUN python3 --version && pip3 --version

ADD /app .
COPY ./requirements.txt .en[v] ./
RUN pip3 install -r requirements.txt

EXPOSE 8000
ENTRYPOINT python3 -m app webapp