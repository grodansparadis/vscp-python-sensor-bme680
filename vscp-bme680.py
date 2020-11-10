#/////////////////////////////////////////////////////////////////////////////
# vscp-bme680.py
#
# This file is part of the VSCP (http://www.vscp.org)
#
# The MIT License (MIT)
#
# Copyright © 2000-2020 Ake Hedman, Grodans Paradis AB <info@grodansparadis.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import getmac
from datetime import datetime

import vscp
import vscp_class as vc
import vscp_type as vt
import vscphelper

import time
     
#import board
#import busio
#import adafruit_bme680

def getGUID(id):
  return 'FF:FF:FF:FF:FF:FF:FF:FE:' + \
  	getmac.get_mac_address().upper() + \
  	":{0:02X}:{1:02X}".format(int(id/256),id & 0xff)

def timestampMillisec64():
    return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000)

# Create library object using our Bus I2C port
#i2c = busio.I2C(board.SCL, board.SDA)
#bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c)
     
# OR create library object using our Bus SPI port
# spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
# bme_cs = digitalio.DigitalInOut(board.D10)
# bme280 = adafruit_bme280.Adafruit_BME280_SPI(spi, bme_cs)
     
# change this to match the location's pressure (hPa) at sea level
#bme680.sea_level_pressure = 1013.25

# Subtract this value from reported temperature
temp_corr = 2.30

# Height at this location
height_at_location = 412.0

# Server and port
host="192.168.1.7:9598"

# Username to login at server
user="admin"

# Password to login at server
password="secret"

# Sensor index for sensor (BME680)
sensorindex=0

# Zone for module
zone=0

# Subzone for module
subzone=0


h1 = vscphelper.newSession()
if (0 == h1 ):
    vscphelper.closeSession(h1)
    raise ValueError('Unable to open vscphelp library session')

print("\n\nConnection in progress...")
rv = vscphelper.open(h1,host,user,password)
if vscp.VSCP_ERROR_SUCCESS == rv :
    print("Command success: open on channel 1")
else:
    vscphelper.closeSession(h1)
    raise ValueError('Command error: open on channel 1  Error code=%d' % rv )

if ( vscp.VSCP_ERROR_SUCCESS == vscphelper.isConnected(h1) ):
    print("CONNECTED!")
else:
    print("DISCONNECTED!")
    raise ValueError('Unable to connect to VSCP server')

rv = vscphelper.noop( h1 )
if vscp.VSCP_ERROR_SUCCESS != rv :
    vscphelper.closeSession(h1)
    raise ValueError('Command error: ''noop''  Error code=%d' % rv )

# -----------------------------------------------------------------------------
#print("\nTemperature: %0.1f C" % (bme680.temperature - temp_corr))
# temperature = "%0.1f".format((bme680.temperature - temp_corr)
temperature = "-27.8"
ex = vscp.vscpEventEx()
# Dumb node, priority normal
ex.head = vscp.VSCP_PRIORITY_NORMAL | vscp.VSCP_HEADER16_DUMB
ex.timestamp = timestampMillisec64()
dt = datetime.utcnow()
ex.year = dt.year
ex.month = dt.month
ex.day = dt.day
ex.hour = dt.hour
ex.minute = dt.minute
ex.second = dt.second
ex.vscpclass = vc.VSCP_CLASS2_MEASUREMENT_STR
ex.vscptype = vt.VSCP_TYPE_MEASUREMENT_TEMPERATURE
# Size is predata + string length + terminating zero
ex.sizedata = 4 + len(temperature) + 1
ex.data[0] = sensorindex
ex.data[1] = zone
ex.data[2] = subzone
ex.data[3] = 1  # unit is degrees Celsius
b = temperature.encode()
for idx in range(len(b)):
    ex.data[idx + 4] = b[idx]
ex.data[4 + len(temperature)] = 0  # optional terminating zero
rv = vscphelper.sendEventEx(h1,ex)
if vscp.VSCP_ERROR_SUCCESS != rv :
    vscphelper.closeSession(h1)
    raise ValueError('Command error: sendEventEx  Error code=%d' % rv )

# -----------------------------------------------------------------------------
# print("Sending Humidity: %0.1f %%" % bme680.humidity)
# humidity = "%0.1f".format(bme680.humidity)
humidity = "1.23"

ex = vscp.vscpEventEx()
# Dumb node, priority normal
ex.head = vscp.VSCP_PRIORITY_NORMAL | vscp.VSCP_HEADER16_DUMB
ex.timestamp = timestampMillisec64()
dt = datetime.utcnow()
ex.year = dt.year
ex.month = dt.month
ex.day = dt.day
ex.hour = dt.hour
ex.minute = dt.minute
ex.second = dt.second
ex.vscpclass = vc.VSCP_CLASS2_MEASUREMENT_STR
ex.vscptype = vt.VSCP_TYPE_MEASUREMENT_HUMIDITY
# Size is predata + string length + terminating zero
ex.sizedata = 4 + len(humidity) + 1
ex.data[0] = sensorindex
ex.data[1] = zone
ex.data[2] = subzone
ex.data[3] = 0  # default unit % of moisture
b = humidity.encode()
for idx in range(len(b)):
    ex.data[idx + 4] = b[idx]
ex.data[4 + len(humidity)] = 0  # optional terminating zero
rv = vscphelper.sendEventEx(h1,ex)
if vscp.VSCP_ERROR_SUCCESS != rv :
    vscphelper.closeSession(h1)
    raise ValueError('Command error: sendEventEx  Error code=%d' % rv )

# -----------------------------------------------------------------------------
#print("Pressure: %0.1f" % bme680.pressure)
# pressure = "%0.3f".format(bme680.pressure*100)
pressure = "102300"

ex = vscp.vscpEventEx()
# Dumb node, priority normal
ex.head = vscp.VSCP_PRIORITY_NORMAL | vscp.VSCP_HEADER16_DUMB
ex.timestamp = timestampMillisec64()
dt = datetime.utcnow()
ex.year = dt.year
ex.month = dt.month
ex.day = dt.day
ex.hour = dt.hour
ex.minute = dt.minute
ex.second = dt.second
ex.vscpclass = vc.VSCP_CLASS2_MEASUREMENT_STR
ex.vscptype = vt.VSCP_TYPE_MEASUREMENT_PRESSURE
# Size is predata + string length + terminating zero
ex.sizedata = 4 + len(pressure) + 1
ex.data[0] = sensorindex
ex.data[1] = zone
ex.data[2] = subzone
ex.data[3] = 0  # default unit Pascal
b = pressure.encode()
for idx in range(len(b)):
    ex.data[idx + 4] = b[idx]
ex.data[4 + len(pressure)] = 0  # optional terminating zero
rv = vscphelper.sendEventEx(h1,ex)
if vscp.VSCP_ERROR_SUCCESS != rv :
    vscphelper.closeSession(h1)
    raise ValueError('Command error: sendEventEx  Error code=%d' % rv )

# -----------------------------------------------------------------------------
#print("Relative pressure = %0.3f hPa" % (bme680.pressure + height_at_location/8.3)*100)
# pressure = "%0.3f".format((bme680.pressure + height_at_location/8.3)*100)
pressure = "1023"

ex = vscp.vscpEventEx()
# Dumb node, priority normal
ex.head = vscp.VSCP_PRIORITY_NORMAL | vscp.VSCP_HEADER16_DUMB
ex.timestamp = timestampMillisec64()
dt = datetime.utcnow()
ex.year = dt.year
ex.month = dt.month
ex.day = dt.day
ex.hour = dt.hour
ex.minute = dt.minute
ex.second = dt.second
ex.vscpclass = vc.VSCP_CLASS2_MEASUREMENT_STR
ex.vscptype = vt.VSCP_TYPE_MEASUREMENT_PRESSURE
# Size is predata + string length + terminating zero
ex.sizedata = 4 + len(pressure) + 1
ex.data[0] = sensorindex + 1
ex.data[1] = zone
ex.data[2] = subzone
ex.data[3] = 0  # default unit Pascal
b = pressure.encode()
for idx in range(len(b)):
    ex.data[idx + 4] = b[idx]
ex.data[4 + len(pressure)] = 0  # optional terminating zero
rv = vscphelper.sendEventEx(h1,ex)
if vscp.VSCP_ERROR_SUCCESS != rv :
    vscphelper.closeSession(h1)
    raise ValueError('Command error: sendEventEx  Error code=%d' % rv )

# -----------------------------------------------------------------------------
# print("Gas = %0.2f ohm" % bme680.gas)
# gas = "%d".format(bme680.altitude)
gas = "150000"

ex = vscp.vscpEventEx()
# Dumb node, priority normal
ex.head = vscp.VSCP_PRIORITY_NORMAL | vscp.VSCP_HEADER16_DUMB
ex.timestamp = timestampMillisec64()
dt = datetime.utcnow()
ex.year = dt.year
ex.month = dt.month
ex.day = dt.day
ex.hour = dt.hour
ex.minute = dt.minute
ex.second = dt.second
ex.vscpclass = vc.VSCP_CLASS2_MEASUREMENT_STR
ex.vscptype = vt.VSCP_TYPE_MEASUREMENT_ELECTRICAL_RESISTANCE
# Size is predata + string length + terminating zero
ex.sizedata = 4 + len(gas) + 1
ex.data[0] = sensorindex
ex.data[1] = zone
ex.data[2] = subzone
ex.data[3] = 0  # default unit Pascal
b = gas.encode()
for idx in range(len(b)):
    ex.data[idx + 4] = b[idx]
ex.data[4 + len(gas)] = 0  # optional terminating zero
rv = vscphelper.sendEventEx(h1,ex)
if vscp.VSCP_ERROR_SUCCESS != rv :
    vscphelper.closeSession(h1)
    raise ValueError('Command error: sendEventEx  Error code=%d' % rv )


rv = vscphelper.close(h1)
if vscp.VSCP_ERROR_SUCCESS != rv :
    vscphelper.closeSession(h1)
    raise ValueError('Command error: close  Error code=%d' % rv )

vscphelper.closeSession(h1)

print("The END")