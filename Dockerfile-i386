FROM monster1025/alpine86-python

ENV LIBRARY_PATH=/lib:/usr/lib

ADD src/requirements.txt /
RUN pip install --upgrade pip && pip install -r /requirements.txt

WORKDIR /app
COPY src /app

CMD ["python", "-u", "/app/main.py"]
