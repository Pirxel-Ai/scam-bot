# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.10-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

ADD main.py .

# Install Git
RUN apt-get update
RUN apt-get -y install git
RUN pip install --upgrade pip
RUN apt-get install ffmpeg libsm6 libxext6  -y

# Install production dependencies.
RUN git clone https://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@github.com/Pirxel-Ai/main-library.git temp
RUN mv temp/src .
RUN mv temp/settings .
#RUN mv temp/*
RUN rm -rf temp

COPY . ./
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python3" "./main.py" ]
#lastly we specified the entry command this line is simply running python ./main.py in our container terminal