# balena-sequencer
Turn a Raspberry Pi 3 into a simple balena-based musical electronic music instrument

![sequencer](https://raw.githubusercontent.com/teotsiv/balena-sequencer/main/photos/box-version.png)

## Overview
Here are the features of the sequencer:
- Produces CD-quality stereophonic audio.
- Usees real audio samples with gapless undetectable looping
- line level audio output
- four sample buttons and dedicated record and loop buttons
- OLED display

## Building the sequencer

The sequencer uses two rotary encoders, six LED momentary switched, an OLED display and a Raspberry Pi 3 B+. Full parts list below. Here is the schematic for wiring it up:

![schematic](https://raw.githubusercontent.com/teotsiv/balena-sequencer/main/photos/schematic.png)

The fully wired unit in a plastic box:

![schematic](https://raw.githubusercontent.com/teotsiv/balena-sequencer/main/photos/insides.png)

You can use any enclosure and be creative! Here is one in a plastic cookie "tin":

![schematic](https://raw.githubusercontent.com/teotsiv/balena-sequencer/main/photos/cookie-version.png)


### Parts list

TBD

## How it works

We use the balena platform to run containers on the device. Each container provides separate functionality.

### [Minio](https://min.io/)
S3 compatible object storage. This provides a web interface for uploading new audio files and their associated jpegs to the device. To access the interface, browse to the local URL using port 9000. To change the username and password, set new values in the `docker-compose.yml` file before first use! (You'll need to clone this repo and push using the CLI in order to do this.) The sound files should be named sound1.wav - sound4.wav and correspond to the preset buttons.

### Webserver
This is a Node/Express webserver that generates a single page for stopping or starting loop playback. It is set to run on port 80 by default and will be displayed if you enable the device's [public URL](https://www.balena.io/docs/learn/develop/runtime/#public-device-urls). (coming soon!)

### Audio
This is our beloved [audio block](https://github.com/balenablocks/audio) that runs a PulseAudio server optimized for balenaOS and is the core of [balenaSound](https://sound.balenalabs.io/). We use it here to take care of setting up and routing all audio needs on the Pi hardware, so the noise container just sends its audio here.

### Controller
A custom Python program that responds to button presses on the control panel, reads the rotary dial position, plays/records the loops, and drives the OLED display.

## How to use
(coming soon)
