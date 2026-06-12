FROM python:3.10.9

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 sshpass -y

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt