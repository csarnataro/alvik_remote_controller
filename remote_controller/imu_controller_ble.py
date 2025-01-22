"""Alvik remote controller

A simple remote controller for Arduino Alvik robot.
Communication with Alvik is done via Bluetooth Low Energy (BLE)

Unlike traditional remote controllers which are using buttons or joystick,
this one is using the Arduino Nano RP2040 Connect builtin inertial measurement unit (IMU)
to drive Alvik. 


Basic features:
- control Alvik just by tilting the controller back/forward and left/right 
- it stops when it loose connection with the remote controller 
- it stops when an obstacle is detected 
- it plays a sound when you push a button


Technical details:
The `asyncio` library is used for managing different tasks in an
asynchronous and independente fashion, so that, for example,
when you honk Alvik's horn, you can still control the speed of the wheels.

The `aioble` library is used to manage the BLE service and all related characteristics.

"""

__author__ = "Christian Sarnataro"
__license__ = "MIT License"
__version__ = "1.0.0"

import time
from lsm6dsox import LSM6DSOX
from micropython import const, alloc_emergency_exception_buf
from machine import Pin, SPI, I2C
import asyncio
import aioble
import bluetooth
import struct

# If an error occurs in an ISR, MicroPython is unable to produce an error
# report unless a special buffer is created for the purpose.
alloc_emergency_exception_buf(100)

led_pin = 6
led = Pin(led_pin, Pin.OUT)
led_on = 0

button_pin = 19
button = Pin(button_pin, Pin.IN, Pin.PULL_UP)

pixels_button_pin = 17
pixels_button = Pin(pixels_button_pin, Pin.IN, Pin.PULL_UP)

# Increase to make Alvik run faster
SPEED_FACTOR = 100

# Under a certains threshold, close to zero, Alvik should stop.
# This will prevent small movements when the IMU will detect very
# small accelerations, e.g. when you keep the controller in your hands
SENSITIVITY_THRESHOLD = 5 


# This is the name used to pair with Alvik's Bluetooth
ADV_NAME = "ALVIK_REMOTE_CONTROLLER"

# Randomly generated UUIDs, they MUST match with the one used on Alvik
_BLE_SERVICE_UUID = bluetooth.UUID('19b10000-e8f2-537e-4f6c-d104768a1214')
_BLE_SPEED_UUID = bluetooth.UUID('19b10001-e8f2-537e-4f6c-d104768a1214')
_BLE_LED_UUID = bluetooth.UUID('19b10002-e8f2-537e-4f6c-d104768a1214')
_BLE_STEERING_UUID = bluetooth.UUID('19b10003-e8f2-537e-4f6c-d104768a1214')
_BLE_HORN_UUID = bluetooth.UUID('19b10004-e8f2-537e-4f6c-d104768a1214')
_BLE_PIXELS_UUID = bluetooth.UUID('19b10005-e8f2-537e-4f6c-d104768a1214')

# How frequently to send advertising beacons.
_ADV_INTERVAL_MS = 250_000

# Initializing and registering the main service and 4 BLE characteristics
ble_service = aioble.Service(_BLE_SERVICE_UUID)
speed_characteristic = aioble.Characteristic(ble_service, _BLE_SPEED_UUID, read=True, notify=True)
steering_characteristic = aioble.Characteristic(ble_service, _BLE_STEERING_UUID, read=True, notify=True)
led_characteristic = aioble.Characteristic(ble_service, _BLE_LED_UUID, read=True, write=True, notify=True, capture=True)
horn_characteristic = aioble.Characteristic(ble_service, _BLE_HORN_UUID, read=True, write=True, notify=True, capture=True)
pixels_characteristic = aioble.Characteristic(ble_service, _BLE_PIXELS_UUID, read=True, write=True, notify=True, capture=True)

aioble.register_services(ble_service)

# Init in I2C mode.
lsm = LSM6DSOX(I2C(0, scl=Pin(13), sda=Pin(12)))

# Helper to encode the data characteristic UTF-8
def _encode_data(data):
    return int(data).to_bytes(2, 'little')

# If acceleration is under a certain threshold, Alvik must stop
# This prevents small movements when the controller is almost horizontal 
def normalize_accel(accel):
    accel = accel * SPEED_FACTOR
    if abs(accel) > SENSITIVITY_THRESHOLD:
        return accel
    return 0
    
def handle_button_press(pin):
    button_pressed = pin.value()
    if button_pressed == 0:
        horn_characteristic.write(_encode_data(1), send_update=True)
        led.value(1)
    else:
        horn_characteristic.write(_encode_data(0), send_update=True)
        led.value(0)
    print('Horn sent to central: ', 1 if button_pressed == 0 else 0)
        
def handle_pixels_button_press(pin):
    button_pressed = pin.value()
    if button_pressed == 0:
        pixels_characteristic.write(_encode_data(1), send_update=True)
        led.value(1)
    else:
        pixels_characteristic.write(_encode_data(0), send_update=True)
        led.value(0)
    print('Pixels sent to central: ', 1 if button_pressed == 0 else 0)


# Interrupts on buttons, to send the correponding characteristic to Alvik
button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=handle_button_press)
pixels_button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=handle_pixels_button_press)

# Controls Alvik's speed.
# Writes current speed to central, by updating the speed characteristic
async def speed_task():
    global led_on
    while True:
        (dir, speed, _) = lsm.accel()
        speed = normalize_accel(speed)
        dir = normalize_accel(dir)
        speed_characteristic.write(_encode_data(speed), send_update=True)
        steering_characteristic.write(_encode_data(dir), send_update=True)
        await asyncio.sleep_ms(100)
        
        
# Creates a connection with Alvik
# Advertises the BLE name and accepts connections from Alvik
async def peripheral_task():
    while True:
        try:
            async with await aioble.advertise(
                _ADV_INTERVAL_MS,
                name=ADV_NAME,
                services=[_BLE_SERVICE_UUID]
            ) as connection:
                print("Connection from: ", connection.device)
                await connection.disconnected()
            
        except asyncio.CancelledError:
            print("Peripheral task cancelled")
        except Exception as e:
            print("Error in peripheral task: ", e)
        finally:
            # Ensure the loop continues to next iteration
            await asyncio.sleep_ms(100)

async def main():
    t1 = asyncio.create_task(peripheral_task())
    t2 = asyncio.create_task(speed_task())
    
    await asyncio.gather(t1, t2)
    
asyncio.run(main())
