FROM balenalib/raspberrypi3-python:3.7-build-20210705

WORKDIR /usr/src/app

RUN \
    apt-get update && apt-get install -y python3-pygame libfreetype6-dev # Needed for Pillow font use

RUN \
    pip3 install numpy pillow adafruit-circuitpython-ssd1306 RPi.GPIO \
    requests redis adafruit-circuitpython-seesaw

COPY *.py ./
COPY *.ttf ./

CMD [ "python3", "sequencer.py" ]

