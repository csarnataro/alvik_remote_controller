import network
import sys
from machine import I2C, Pin
from arduino_alvik import ArduinoAlvik
from modulino import ModulinoBuzzer, ModulinoPixels, ModulinoColor
from time import sleep_ms, sleep, ticks_ms, ticks_diff
from math import cos, pi
from melodies import pacman
import ustruct
import bluetooth
import asyncio
import aioble


ADV_NAME = "ALVIK_REMOTE_CONTROLLER"

_BLE_SERVICE_UUID = bluetooth.UUID('19b10000-e8f2-537e-4f6c-d104768a1214')
_BLE_SPEED_UUID = bluetooth.UUID('19b10001-e8f2-537e-4f6c-d104768a1214')
_BLE_LED_UUID = bluetooth.UUID('19b10002-e8f2-537e-4f6c-d104768a1214')
_BLE_STEERING_UUID = bluetooth.UUID('19b10003-e8f2-537e-4f6c-d104768a1214')
_BLE_HORN_UUID = bluetooth.UUID('19b10004-e8f2-537e-4f6c-d104768a1214')
_BLE_PIXELS_UUID = bluetooth.UUID('19b10005-e8f2-537e-4f6c-d104768a1214')

left_speed = 0
right_speed = 0
# Increase to make Alvik run faster, but harder to control
SPEED_FACTOR = 0.7


# Initialize Alvik
alvik = ArduinoAlvik()
alvik.begin()
buzzer = ModulinoBuzzer(I2C(0, scl=Pin(12, Pin.OUT), sda=Pin(11, Pin.OUT)))
pixels = ModulinoPixels(I2C(0, scl=Pin(12, Pin.OUT), sda=Pin(11, Pin.OUT)))
sleep(1)  # Waiting for the robot to setup

is_playing = False
is_pixels_on = False

# Helper to decode the characteristic encoding (bytes).
def _decode_data(data):
    try:
        if data is not None:
            # Decode the UTF-8 data
            number = ustruct.unpack("<h", data)[0]
            return number
    except Exception as e:
        print("Error decoding temperature:", e)
        return None

async def find_tx_device():
    # Scan for 5 seconds, in active mode, with very low interval/window (to
    # maximise detection rate).
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            print("Device: ", result.name())
            # See if it matches our name and the environmental sensing service.
            if result.name() == ADV_NAME:
               return result.device
    return None

async def pixels_task():
    global is_pixels_on
    while True:
        if is_pixels_on:
            await start_pixels_animation()
            is_pixels_on = False
        else:
            await stop_pixels_animation()
        await asyncio.sleep_ms(300)

async def horn_task():
    global is_playing
    while True:
        if is_playing:
            await play_tune(buzzer.tone)
            is_playing = False

        await asyncio.sleep_ms(300)
    

async def speed_task():
    global is_playing
    global is_pixels_on
    
    print("In speed_task")
    device = await find_tx_device()
    while not device:
        print("Remote controller not found")
        device = await find_tx_device()
        await asyncio.sleep_ms(2000)

    try:
        print("Connecting to", device)
        connection = await device.connect()
    except asyncio.TimeoutError:
        print("Timeout during connection")
        return
    
    async with connection:
        
        try:
            dev_service = await connection.service(_BLE_SERVICE_UUID)
            speed_characteristic = await dev_service.characteristic(_BLE_SPEED_UUID)
            steering_characteristic = await dev_service.characteristic(_BLE_STEERING_UUID)
            horn_characteristic = await dev_service.characteristic(_BLE_HORN_UUID)
            pixels_characteristic = await dev_service.characteristic(_BLE_PIXELS_UUID)
            while connection.is_connected():
                alvik.left_led.set_color(0, 1, 0)
              
                horn_as_bytes = await horn_characteristic.read()
                horn = _decode_data(horn_as_bytes)

                if horn == 1:
                    is_playing = True
                
                
                pixels_as_bytes = await pixels_characteristic.read()
                pixels = _decode_data(pixels_as_bytes)
                if pixels == 1: # we've received a "push" event
                    is_pixels_on = not is_pixels_on
                
                
                speed_as_bytes = await speed_characteristic.read()
                speed = _decode_data(speed_as_bytes)

                dir_as_bytes = await steering_characteristic.read()
                dir = _decode_data(dir_as_bytes)

                left_wheel_speed = (speed + (speed * (dir/100))) * SPEED_FACTOR
                right_wheel_speed = (speed - (speed * (dir/100))) * SPEED_FACTOR
                # print("Speed is: ", speed, left_wheel_speed, left_wheel_speed)
                
                alvik.set_wheels_speed(left_wheel_speed, right_wheel_speed)
        except asyncio.TimeoutError:
            print("Timeout discovering services/characteristics")
            print("Disconnected, should stop the robot for safety reason")
            alvik.left_led.set_color(1, 0, 0)
            alvik.brake()
            stop_pixels_animation()
            return
  
  
async def stop_pixels_animation():
    pixels.clear_all()
    pixels.show()
    
async def start_pixels_animation():
    global is_pixels_on
    color = (255, 0, 0) # red color
    wait = 50 # speed
    barLength = 4 # how many pixels are lit at the same time, going back and forth
    

    while True and is_pixels_on:
        # Move the bar forward
        for i in range(8):
            for k in range(barLength):
                if i + k < 8:
                    pixels.set_rgb(i + k, *color)
            pixels.show()
            await asyncio.sleep_ms(wait)
            for j in range(8):
                pixels.clear(j)
            
        # Move the bar backward
        for i in range(8 - 1, -1, -1):
            for k in range(barLength):
                if i - k >= 0:
                    pixels.set_rgb(i - k, *color)
            pixels.show()
            await asyncio.sleep_ms(wait)
            for j in range(8):
                pixels.clear(j)
                
    stop_pixels_animation()
    

async def play_tune(tune_function):

    tempo = 105
    wholenote = int((60000 * 4) / tempo)

    divider = 0
    noteDuration = 0

    for note, divider in pacman:
        if divider > 0:
            noteDuration = int(wholenote / divider)
        elif divider < 0:
            # dotted notes last a little bit longer
            noteDuration = -1 * int(wholenote / divider)
            noteDuration *= 1.25

        tune_function(note, blocking=False)
        await asyncio.sleep_ms(int(noteDuration * 0.9))

        tune_function(ModulinoBuzzer.NOTES["REST"], blocking=False)
        await asyncio.sleep_ms(int(noteDuration * 0.1))


async def main():
    alvik.brake()
    stop_pixels_animation()
    alvik.left_led.set_color(1, 0, 0)
    
    t1 = asyncio.create_task(speed_task())
    t2 = asyncio.create_task(horn_task())
    t3 = asyncio.create_task(pixels_task())
    
    await asyncio.gather(t1, t2, t3)
  
asyncio.run(main())


