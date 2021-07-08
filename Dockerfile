#FROM jrottenberg/ffmpeg:4.1-alpine
FROM kolisko/rpi-ffmpeg:latest


FROM python:3.9.2

RUN pip3 install --no-cache requests
RUN pip3 install --no-cache ffmpeg-normalize
COPY --from=0 /usr/local/ /usr/local
COPY --from=0 /usr/lib/ /usr/lib
COPY --from=0 /lib/ /lib


COPY requirements.txt /
RUN pip3 install --no-cache -r /requirements.txt

WORKDIR /
ENTRYPOINT ["python3", "main.py"]

COPY download_sounds.py /
RUN python3 download_sounds.py

COPY main.py /
COPY cogs /cogs
