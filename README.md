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


### Parts list

The sequencer uses two rotary encoders, six LED momentary switched, an OLED display and a Raspberry Pi 3 B+. Full parts list below.

- two [rotary encoder](https://www.adafruit.com/product/377)
- two [I2C rotary breakout boards](https://www.adafruit.com/product/4991)
- one [OLED display](https://www.adafruit.com/product/326)
- one Raspberry Pi 3, 4 or Zero 2W
- six variuos colored LED momentary pushbuttons such as [these](https://www.adafruit.com/product/1439)
- six 220 ohm resistors, one for each button's LED
- a suitable case, wires, jumper cables

Here is the schematic for wiring it up:

![schematic](https://raw.githubusercontent.com/teotsiv/balena-sequencer/main/photos/schematic.png)

There are many ways to wire it up as long as you follow the diagram above. Here is an example of a fully wired unit in a plastic box:

![schematic](https://raw.githubusercontent.com/teotsiv/balena-sequencer/main/photos/insides.png)

You can use any enclosure and be creative! Here is one in a plastic cookie "tin":

![schematic](https://raw.githubusercontent.com/teotsiv/balena-sequencer/main/photos/cookie-version.png)

### Software setup

Running this project is as simple as deploying it to a fleet.

One-click deploy to balenaCloud:

[![balena deploy button](https://www.balena.io/deploy.svg)](https://dashboard.balena-cloud.com/deploy?repoUrl=https://github.com/Teotsiv/balena-sequencer)

or

Sign up at [balena.io](www.balena.io) and follow our [Getting Started Guide](https://www.balena.io/docs/learn/getting-started/raspberrypi3/python/).
- Clone this repository to your local workspace.
- Using the [Balena CLI](https://www.balena.io/docs/reference/balena-cli/), push the code with `balena push <fleet-name>`.

## How it works

We use the [balena platform](www.balena.io) to run containers on the device. Each container provides separate functionality:

### [Minio](https://min.io/)
S3 compatible object storage. This provides a web interface for uploading new audio files to the device. To access the interface, browse to the local URL using port 9000. To change the username and password, set new values in the `docker-compose.yml` file before first use! (You'll need to clone this repo and push using the CLI in order to do this.) The sound files should be named sound1.wav, sound2.wav, sound3.wav sound4.wav which correspond to the four sample buttons.

### Audio
This is our beloved [audio block](https://github.com/balenablocks/audio) that runs a PulseAudio server optimized for balenaOS and is the core of [balenaSound](https://sound.balenalabs.io/). We use it here to take care of setting up and routing all audio needs on the Pi hardware, so the noise container just sends its audio here.

### Controller
A custom Python program that responds to button presses on the control panel, reads the rotary dial position, plays/records the loops, and drives the OLED display.

## How to use

Power up the device and connect an audio amplifier or powered speakers to the Pi's audio out jack. Once the device is ready, the button LEDs will flash in sequence. Upload one or more wav files using the instructions above. Once the files are loaded, you can play them back by pressing the appropriate preset button. To record a loop, press the "rec" button and then play your beat using the preset buttons. When you are done, press the "rec" button again to stop. To play back your sequence, press the "play" button. While the loop is playing, you can turn the "tempo" rotary control to play the loop faster or slower.

