import network
import sys
from machine import I2C, Pin
from arduino_alvik import ArduinoAlvik
from modulino import ModulinoBuzzer
from time import sleep_ms, sleep, ticks_ms, ticks_diff
from math import cos, pi
from play_tune import play_tune
import ustruct
import bluetooth
import asyncio
import aioble


MIN_DISTANCE = 6 
TIMEOUT = 1000
ADV_NAME = "ALVIK_REMOTE_CONTROLLER"

_BLE_SERVICE_UUID = bluetooth.UUID('19b10000-e8f2-537e-4f6c-d104768a1214')
_BLE_SPEED_CHAR_UUID = bluetooth.UUID('19b10001-e8f2-537e-4f6c-d104768a1214')
_BLE_LED_UUID = bluetooth.UUID('19b10002-e8f2-537e-4f6c-d104768a1214')

message_received = -TIMEOUT

left_speed = 0
right_speed = 0


# Initialize Alvik
alvik = ArduinoAlvik()
alvik.begin()
buzzer = ModulinoBuzzer(I2C(0, scl=Pin(12, Pin.OUT), sda=Pin(11, Pin.OUT)))
sleep(1)  # Waiting for the robot to setup

# Calibrate color sensor for white
alvik.color_calibration("white")



# Helper to decode the LED characteristic encoding (bytes).
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


async def main():
    print("In main")
    device = await find_tx_device()
    while not device:
        print("Speed sensor not found")
        device = await find_tx_device()
        await asyncio.sleep_ms(2000)
#        return

    try:
        print("Connecting to", device)
        connection = await device.connect()
    except asyncio.TimeoutError:
        print("Timeout during connection")
        return
    
    async with connection:
        
        try:
            dev_service = await connection.service(_BLE_SERVICE_UUID)
            speed_characteristic = await dev_service.characteristic(_BLE_SPEED_CHAR_UUID)
            while connection.is_connected():
              
                speed_as_bytes = await speed_characteristic.read()
                speed = _decode_data(speed_as_bytes)
                print("Speed is: ", speed)
                alvik.set_wheels_speed(speed * 0.3, speed * 0.3)
        except asyncio.TimeoutError:
            print("Timeout discovering services/characteristics")
            print("Disconnected, should stop the robot for safety reason")
            return
                
    
    
asyncio.run(main())


