FROM alpine:3.15
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD . /code/
RUN apk update && \
apk add --update gcc libc-dev linux-headers && rm -rf /var/cache/apk/* && \
apk add zlib lzo-dev && \
apk add --update --no-cache python3-dev && ln -sf python3 /usr/bin/python && \
python3 -m ensurepip && \
pip3 install --no-cache --upgrade pip setuptools && \
pip3 install -r requirements1.txt && \
pip3 install -r requirements2.txt

