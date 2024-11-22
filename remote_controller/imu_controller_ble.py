import time
from lsm6dsox import LSM6DSOX
from micropython import const
from machine import Pin, SPI, I2C
import asyncio
import aioble
import bluetooth
import struct

led_pin = 6
led = Pin(led_pin, Pin.OUT)
led_on = 0

ADV_NAME = "ALVIK_REMOTE_CONTROLLER"
_BLE_SERVICE_UUID = bluetooth.UUID('19b10000-e8f2-537e-4f6c-d104768a1214')
_BLE_SPEED_CHAR_UUID = bluetooth.UUID('19b10001-e8f2-537e-4f6c-d104768a1214')
_BLE_LED_UUID = bluetooth.UUID('19b10002-e8f2-537e-4f6c-d104768a1214')
# How frequently to send advertising beacons.
_ADV_INTERVAL_MS = 250_000

ble_service = aioble.Service(_BLE_SERVICE_UUID)
speed_characteristic = aioble.Characteristic(ble_service, _BLE_SPEED_CHAR_UUID, read=True, notify=True)
led_characteristic = aioble.Characteristic(ble_service, _BLE_LED_UUID, read=True, write=True, notify=True, capture=True)

aioble.register_services(ble_service)

# Init in I2C mode.
lsm = LSM6DSOX(I2C(0, scl=Pin(13), sda=Pin(12)))

# Helper to encode the data characteristic UTF-8
def _encode_data(data):
    return int(data).to_bytes(2, 'little')

def normalize_speed(speed):
    speed = speed * 100
    if abs(speed) > 5:
        return speed
    return 0
    

# Write current speed to central, by updating the speed characteristic
async def speed_task():
    global led_on
    while True:
        time.sleep_ms(300)
        if led_on == 1:
            led_on = 0
        else:
            led_on = 1
        led.value(led_on)

        (_, speed, _) = lsm.accel()
        speed = normalize_speed(speed)
        speed_characteristic.write(_encode_data(speed), send_update=True)
        print('Speed sent to central: ', speed)
        await asyncio.sleep_ms(200)
        
        
        
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
    t1 = asyncio.create_task(speed_task())
    t2 = asyncio.create_task(peripheral_task())
    
    await asyncio.gather(t1, t2)
    
asyncio.run(main())


# while (True):
# #    calc_speed()
# #     gyro = lsm.gyro()
# #     (x, z, y) = gyro
# #     print('x:{:>8.3f} y:{:>8.3f} z:{:>8.3f}'.format(*gyro))
# #
#     (dir, speed, _) = lsm.accel()
#     
#     print(f'dir:{dir},speed:{speed}')
#     time.sleep_ms(300)
#     if led_on == 1:
#         led_on = 0
#     else:
#         led_on = 1
#     led.value(led_on)
        
        


