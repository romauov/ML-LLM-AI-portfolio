FROM registry.m16.tech/ml-lib:3

WORKDIR /app

RUN apt-get update && apt-get install sshpass

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir /home/user && chown -R 1000:1000 /home/user
RUN echo "user:x:1000:1000:user:/home/user:/bin/bash" >> /etc/passwd
RUN mkdir /home/user/.cache && chown -R 1000:1000 /home/user/.cache
