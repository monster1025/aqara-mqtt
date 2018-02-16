FROM arm32v7/python:slim

ENV LIBRARY_PATH=/lib:/usr/lib

ADD src/requirements.txt /
RUN apt-get update && apt-get install -y build-essential autoconf \
	&& pip install --upgrade pip && pip install -r /requirements.txt \ 
	&& apt-get remove -y build-essential autoconf \
	&& apt-get autoremove -y \
  	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY src /app

CMD ["python3", "-u", "/app/main.py"]