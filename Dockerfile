FROM python:3.8.6-alpine3.12

RUN echo 'https://mirrors.aliyun.com/alpine/v3.12/main/' > /etc/apk/repositories \
 && echo 'https://mirrors.aliyun.com/alpine/v3.12/community/' >> /etc/apk/repositories \
 && apk add alpine-sdk libffi-dev openssl-dev postgresql-dev

WORKDIR /data
COPY requirements.txt /data/requirements.txt
RUN pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && pip3 install -r requirements.txt

COPY . /data
RUN cp config.sample.py config.py

ENTRYPOINT ["python3", "script.py"]

CMD ["app.py"]
