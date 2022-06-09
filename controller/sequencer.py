# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import time 
import datetime
import RPi.GPIO as GPIO 
from adafruit_seesaw import seesaw, rotaryio, seesaw as seesaws
import pygame
from pathlib import Path

#### variables and constants... ####

# button constants
P1_GPIO = 13  # GPIO of sound1
P2_GPIO = 26
P3_GPIO = 19
P4_GPIO = 21
LOOP_GPIO = 5
REC_GPIO = 6
SLEEP_LIMIT = 600  # Seconds until OLED screen saver (0 = none)
DEBOUNCE = 500  # switch debounce time in ms

tempo = 0  # initial tempo adj in % (-100 to 100)
demo_mode = True  # demo mode: all LEDs blink
volume = 75  # initial volume in %
position_v = -1  # keeps track of volume rotary pos
position_t = -1  # keeps track of tempo rotary pos
sleep_time = 0
loop_count = 0  # Counts number of loops played back

# for recording:
recording = []  # list of elapsed times and sound numbers
mymode = "idle"  # mode options: idle, loop, record
rec_start = datetime.datetime.now()  # start of most recent recording
elapsed = 0 # milliseconds of elapsed recording time

# For oled display...
# Define the Reset Pin
oled_reset = digitalio.DigitalInOut(board.D4)

# Change these
# to the right size for your display!
WIDTH = 128
HEIGHT = 64  # Usually 32 or 64
BORDER = 5

# Use for OLED I2C.
i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C, reset=oled_reset)

# Clear display.
oled.fill(0)
oled.show()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
image = Image.new("1", (oled.width, oled.height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a white background
draw.rectangle((0, 0, oled.width, oled.height), outline=255, fill=255)

# Draw a smaller inner rectangle
draw.rectangle(
    (BORDER, BORDER, oled.width - BORDER - 1, oled.height - BORDER - 1),
    outline=0,
    fill=0,
)

# image for blanking text area
img_blank = Image.new("1", (oled.width - BORDER - 1, oled.height - BORDER - 1))

# Adafruit I2C QT Rotary Encoder - volume
# Using the INT output on Pi GPIO 17
try:
    seesaw = seesaw.Seesaw(i2c, addr=0x36)
except:
    print("Error initializing rotary volume encoder board.")
else:
    seesaw_product = (seesaw.get_version() >> 16) & 0xFFFF
    print("Found volume seesaw supported product {}".format(seesaw_product))
    if seesaw_product != 4991:
        print("Wrong firmware loaded for volume QT encoder?  Expected 4991")
    # Set up the rotary click button, and add to interrupt
    seesaw.pin_mode(24, seesaw.INPUT_PULLUP)  # Pin on the QT
    seesaw.set_GPIO_interrupts(1 << 24, True)
    seesaw.enable_encoder_interrupt()

# Adafruit I2C QT Rotary Encoder - tempo
# Using the INT output on Pi GPIO 24 (not to be confused with QT pin 24 below)
try:
    seesaw2 = seesaws.Seesaw(i2c, addr=0x37)
except Exception as e:
    print("Error initializing rotary tempo encoder board: {}".format(e))
else:
    seesaw_product = (seesaw2.get_version() >> 16) & 0xFFFF
    print("Found tempo seesaw supported product {}".format(seesaw_product))
    if seesaw_product != 4991:
        print("Wrong firmware loaded for tempo QT encoder?  Expected 4991")
    # Set up the rotary click button, and add to interrupt
    seesaw2.pin_mode(24, seesaw2.INPUT_PULLUP)  # Pin on the QT
    seesaw2.set_GPIO_interrupts(1 << 24, True)
    seesaw2.enable_encoder_interrupt()

# Set up audio
# This sequence reduces latency. See https://stackoverflow.com/a/34324343
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()
pygame.init()


try:
    sound_level = float(os.getenv('SOUND_LEVEL', '0.2'))
except Exception as e:
    print("Invalid or no value for SOUND_LEVEL. Using default 0.2")
    sound_level = 0.2

# load sounds, set volume
check_file = Path("/data/my_data/sounds/sound1.wav")
if check_file.is_file():
    snd_1 = pygame.mixer.Sound("/data/my_data/sounds/sound1.wav")
    pygame.mixer.Sound.set_volume(snd_1, sound_level)
else:
    snd_1 = None
check_file = Path("/data/my_data/sounds/sound2.wav")
if check_file.is_file():
    snd_2 = pygame.mixer.Sound("/data/my_data/sounds/sound2.wav")
    pygame.mixer.Sound.set_volume(snd_2, sound_level)
else:
    snd_2 = None
check_file = Path("/data/my_data/sounds/sound3.wav")
if check_file.is_file():
    snd_3 = pygame.mixer.Sound("/data/my_data/sounds/sound3.wav")
    pygame.mixer.Sound.set_volume(snd_3, sound_level)
else:
    snd_3 = None
check_file = Path("/data/my_data/sounds/sound4.wav")
if check_file.is_file():
    snd_4 = pygame.mixer.Sound("/data/my_data/sounds/sound4.wav")
    pygame.mixer.Sound.set_volume(snd_4, sound_level)
else:
    snd_4 = None

def end_demo():

    #
    # Ends demo mode
    #   
    global demo_mode
    if demo_mode:
        time.sleep(0.66)
        demo_mode = False
        # end demo and turn off LEDs
        all_leds_off()

def all_leds_off():

    #
    # Turns off all button LEDs
    #
    GPIO.output(16, GPIO.LOW)
    GPIO.output(14, GPIO.LOW)
    GPIO.output(15, GPIO.LOW)
    GPIO.output(18, GPIO.LOW)
    GPIO.output(23, GPIO.LOW)
    GPIO.output(12, GPIO.LOW)

def oled_draw(my_text):
    
    #
    # Draw text on the OLED
    # Currently just one line in center
    #
    global image, draw
    # Clear display.
    image.paste(img_blank, (BORDER, BORDER))
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    (font_width, font_height) = font.getsize(my_text)
    draw.text(
        (oled.width // 2 - font_width // 2, oled.height // 2 - font_height // 2),
        my_text,
        font=font,
        fill=255,
    )
    # Display image
    oled.image(image)
    oled.show()

def button_rec(channel):

    #
    # Stops/starts recording
    # Runs on rec button callback
    #
    global recording, mymode, rec_start

    end_demo()
    print("Rec button pressed")
    if mymode == "record":
        # After recording is stopped, elapsed = total length of recording
        elapsed = (datetime.datetime.now() - rec_start).total_seconds() * 1000
        GPIO.output(15, GPIO.LOW)
        oled_draw("idle - ready.")
        mymode = "idle"
    else:
        all_leds_off()
        mymode = "record"
        GPIO.output(15, GPIO.HIGH)
        oled_draw("recording...")
        recording.clear()
        rec_start = datetime.datetime.now()
        
    
def button_loop(channel):

    #
    # Starts/stops playing the loop
    # Fires on loop button callback
    #
    global mymode, loop_count

    end_demo()
    print("Loop button pressed")
    if mymode == "loop":
        # turn off looping
        mymode = "idle"
        all_leds_off()
        loop_count = 0
        oled_draw("idle: ready")
    else:
        all_leds_off()
        if len(recording) > 0:
            mymode = "loop"
            GPIO.output(14, GPIO.HIGH)
            oled_draw("looping...")
        else:
            print("Nothing to loop!")
            oled_draw("No loop!")

    

def play_loop():

    #
    # Plays the loop once
    # Uses data stored in recording list
    # Adjusts temp based on tempo value
    # 
    # https://stackoverflow.com/questions/16789776/iterating-over-two-values-of-a-list-at-a-time-in-python
    it = iter(recording)
    last_wait = 0
    last_x = 0
    sleep_time = 0
    for x in it:
        wait_time = next(it)
        print("looping ch:{0}, wait: {1}".format(x, wait_time / 1000))
        sleep_time = (wait_time - last_wait) / 1000
        time.sleep(sleep_time * ((tempo / 100) + 1))
        if last_x == 13: GPIO.output(18, GPIO.LOW)
        if last_x == 26: GPIO.output(23, GPIO.LOW)
        if last_x == 19: GPIO.output(12, GPIO.LOW)
        if last_x == 21: GPIO.output(16, GPIO.LOW)
        last_wait = wait_time
        if x == 13:
            if snd_1 != None:
                GPIO.output(18, GPIO.HIGH)
                pygame.mixer.Sound.play(snd_1)
        if x == 26:
            if snd_2 != None:
                GPIO.output(23, GPIO.HIGH)
                pygame.mixer.Sound.play(snd_2)
        if x == 19:
            if snd_3 != None:
                GPIO.output(12, GPIO.HIGH)
                pygame.mixer.Sound.play(snd_3)
        if x == 21:
            if snd_4 != None:
                GPIO.output(16, GPIO.HIGH)
                pygame.mixer.Sound.play(snd_4)
        last_x = x  

    if last_x == 13: GPIO.output(18, GPIO.LOW)
    if last_x == 26: GPIO.output(23, GPIO.LOW)
    if last_x == 19: GPIO.output(12, GPIO.LOW)
    if last_x == 21: GPIO.output(16, GPIO.LOW)
          
def button_preset(channel):

    #
    # Plays preset sound
    # Also adds to recording list if in record mode
    # Fires on any preset button callback
    #
    global recording, elapsed

    if mymode == "record": 
        elapsed = (datetime.datetime.now() - rec_start).total_seconds() * 1000
        print("recording, ch:{0}, start:{1}, lap:{2}".format(channel, rec_start, elapsed))
    else:
        print("Preset button {} pressed".format(channel))
    end_demo()
    
    if channel == 13:
        if snd_1 != None:
            pygame.mixer.Sound.play(snd_1)
    if channel == 26:
        if snd_2 != None:
            pygame.mixer.Sound.play(snd_2)
    if channel == 19:
        if snd_3 != None:
            pygame.mixer.Sound.play(snd_3)
    if channel == 21:
        if snd_4 != None:
            pygame.mixer.Sound.play(snd_4)

    if mymode == "record":
        recording.append(channel)
        recording.append(elapsed)

def rotary_volume(r):

    #
    # Triggered by rotary QT interrupt
    # when rotary volume wheel is turned or clicked
    #
    global volume, position_v

    end_demo()
    current_pos = seesaw.encoder_position()
    vol_btn = not(seesaw.digital_read(24))
    #print("vol: {0}; current_pos: {1}; rot_btn: {2}".format(volume, current_pos, vol_btn))
    if current_pos == position_v:
        if vol_btn == True:
            print("Volume button pressed!")
            volume = 75
            oled_draw("vol: 75 %")
            #button_rotary_click()
    else:
        if current_pos < position_v:
            #print("Volume turned right {}".format(current_pos))
            # Action on every other (even) click
            if (current_pos % 2) == 0:
                volume = volume + 1
                oled_draw("vol: {} %".format(volume))
        else:
            #print("Volume turned left {}".format(current_pos))
            # Action on every other (even) click
            if (current_pos % 2) == 0:
                volume = volume - 1
                oled_draw("vol: {} %".format(volume))
    position_v = current_pos

def rotary_tempo(r):

    #
    # Triggered by rotary QT interrupt
    # when rotary tempo wheel is turned or clicked
    #
    global tempo, position_t

    end_demo()
    current_pos = seesaw2.encoder_position()
    tempo_btn = not(seesaw2.digital_read(24))
    tempo_draw = "tempo: "
    #print("tempo: {0}; current_pos: {1}; rot_btn: {2}".format(tempo, current_pos, tempo_btn))
    if current_pos == position_t:
        if tempo_btn == True:
            print("Tempo button pressed!")
            tempo = 0
            oled_draw("tempo: 0 %")
    else:
        if current_pos < position_t:
            #print("Tempo turned right {}".format(current_pos))
            # Action on every other (even) click
            if (current_pos % 2) == 0:
                tempo = tempo - 1
                if tempo < 0:
                    oled_draw("tempo: +{} %".format(-tempo))
                else:
                    oled_draw("tempo: {} %".format(-tempo))
        else:
            #print("Tempo turned left {}".format(current_pos))
            # Action on every other (even) click
            if (current_pos % 2) == 0:
                tempo = tempo + 1
                if tempo < 0:
                    oled_draw("tempo: +{} %".format(-tempo))
                else:
                    oled_draw("tempo: {} %".format(-tempo))

    position_t = current_pos

oled_draw("Welcome!")

# Set button inputs
# stop
GPIO.setup(REC_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(REC_GPIO, GPIO.RISING, callback=button_rec, bouncetime=DEBOUNCE)

#display
GPIO.setup(LOOP_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(LOOP_GPIO, GPIO.RISING, callback=button_loop, bouncetime=DEBOUNCE+200)

# preset 1
GPIO.setup(P1_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(P1_GPIO, GPIO.RISING, callback=button_preset, bouncetime=DEBOUNCE)

# preset 2
GPIO.setup(P2_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(P2_GPIO, GPIO.RISING, callback=button_preset, bouncetime=DEBOUNCE)

# preset 3
GPIO.setup(P3_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(P3_GPIO, GPIO.RISING, callback=button_preset, bouncetime=DEBOUNCE)

#preset 4
GPIO.setup(P4_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(P4_GPIO, GPIO.RISING, callback=button_preset, bouncetime=DEBOUNCE)

#rotaryio interrupt
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(17, GPIO.FALLING, callback=rotary_volume)

GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(27, GPIO.FALLING, callback=rotary_tempo)

# Set LED outputs
GPIO.setup(14, GPIO.OUT) # 1
GPIO.setup(15, GPIO.OUT) # 2
GPIO.setup(18, GPIO.OUT) # 3
GPIO.setup(23, GPIO.OUT) # 4
GPIO.setup(12, GPIO.OUT) # 5
GPIO.setup(16, GPIO.OUT) # 6


# initial startup - loop demo mode
while demo_mode:

    if demo_mode: GPIO.output(14, GPIO.HIGH) # Square
    GPIO.output(16, GPIO.LOW) # Square
    time.sleep(0.3)
    if demo_mode: GPIO.output(15, GPIO.HIGH) # Square
    GPIO.output(14, GPIO.LOW) # Square
    time.sleep(0.3)
    if demo_mode: GPIO.output(18, GPIO.HIGH) # Square
    GPIO.output(15, GPIO.LOW) # Square
    time.sleep(0.3)
    if demo_mode: GPIO.output(23, GPIO.HIGH) # Square
    GPIO.output(18, GPIO.LOW) # Square
    time.sleep(0.3)
    if demo_mode: GPIO.output(12, GPIO.HIGH)
    GPIO.output(23, GPIO.LOW) # Square
    time.sleep(0.3)
    if demo_mode: GPIO.output(16, GPIO.HIGH) # Square
    GPIO.output(12, GPIO.LOW) # Square
    time.sleep(0.4)

while True:

    # main loop

    if mymode == "record":
        oled_draw("recording {} s".format(int(elapsed/1000)))
        print("recording")

        time.sleep(1)

    elif mymode == "loop":

        print("Playing loop")
        loop_count = loop_count + 1
        if loop_count > 10000: loop_count = 0
        oled_draw("loop #{}".format(loop_count))
        play_loop()
    else:
        print("Idle: sleeping")
        time.sleep(1)
