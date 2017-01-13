#for x86
FROM monster1025/alpine86-python

#for x64
#FROM jfloff/alpine-python:3.4

ENV LIBRARY_PATH=/lib:/usr/lib

ADD src/requirements.txt /
RUN pip install --upgrade pip && pip install -r /requirements.txt

WORKDIR /app
COPY src /app
ADD config.yaml /app/

CMD ["python", "-u", "/app/main.py"]