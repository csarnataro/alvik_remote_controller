# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT
"""
`hs3003`
================================================================================

MicroPython Driver for the Renesas HS3003 Temperature and Humidity Sensor


* Author(s): Jose D. Montoya


"""

try:
    from typing import Tuple
except ImportError:
    pass
import time

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/jposada202020/MicroPython_HS3003.git"


class HS3003:
    """Driver for the HS3003 Sensor connected over I2C.
    Resolution can be configured, however this is not implemented in this library,
    as is required to send commands after power up, to put the sensor in
    programming mode

    :param ~machine.I2C i2c: The I2C bus the HS3003 is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x44`

    **Quickstart: Importing and using the device**

    Here is an example of using the :class:`HS3003` class.
    First you will need to import the libraries to use the sensor

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_hs3003 import hs3003

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        hs = hs3003.HS3003(i2c)

    Now you have access to the attributes

    .. code-block:: python

        temp = hs.temperature
        humidity = hs.relative_humidity

    """

    def __init__(self, i2c, address: int = 0x44) -> None:
        self._i2c = i2c
        self._address = address
        self._status_bit = None

    @property
    def measurements(self) -> Tuple[float, float]:
        """
        Return Temperature and Relative Humidity
        """
        self._i2c.writeto(self._address, bytes([0x00]))
        time.sleep(0.1)  # Time to wake up the sensor
        data = bytearray(4)
        self._i2c.readfrom_into(self._address, data)

        # The Status bit will have a value of 1 when the data is stalled
        self._status_bit = data[0] & 0x40

        msb_humidity = data[0] & 0x3F
        lsb_humidity = data[1]
        raw_humidity = msb_humidity << 8 | lsb_humidity
        humidity = (raw_humidity / (2**14.0 - 1)) * 100

        msb_temperature = data[2]
        lsb_temperature = (data[3] & 0xFC) >> 2
        raw_temperature = msb_temperature << 6 | lsb_temperature
        temperature = (raw_temperature / (2**14.0 - 1)) * 165 - 40

        return temperature, humidity

    @property
    def relative_humidity(self) -> float:
        """The current relative humidity in % rH"""
        return self.measurements[1]

    @property
    def temperature(self) -> float:
        """The current temperature in Celsius"""
        return self.measurements[0]
