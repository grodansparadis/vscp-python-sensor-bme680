###############################################################################
# mqtt-bme680.py
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

import sys
import configparser
import getopt

#import getmac
import vscp
import vscp_class as vc
import vscp_type as vt
import vscphelper
import paho.mqtt.client as mqtt

import time

# Set to True to run with simulated data
bDebug = True

config = configparser.ConfigParser()

if not bDebug :
    import board
    import busio
    import adafruit_bme680

def usage():
    print("usage: mqtt-bm680.py -v -c <pat-to-config-file> -h ")
    print("---------------------------------------------")
    print("-h/--help    - This text.")
    print("-v/--verbose - Print output also to screen.")
    print("-c/--config  - Path to configuration file.")

# Initialize VSCP event content
def initEvent(ex,id,vscpClass,vscpType):
    # Dumb node, priority normal
    ex.head = vscp.VSCP_PRIORITY_NORMAL | vscp.VSCP_HEADER16_DUMB
    g = vscp.guid()
    g.setGUIDFromMAC(id)
    ex.guid = g.guid
    ex.vscpclass = vscpClass
    ex.vscptype = vscpType

# def getFloatByteArray :
#     return bytearray(struct.pack("f", value))  

# Create library object using our Bus I2C port
if not bDebug :
    i2c = busio.I2C(board.SCL, board.SDA)
    bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c)
     
# OR create library object using our Bus SPI port
# if not bDebug :
#   spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
#   bme_cs = digitalio.DigitalInOut(board.D10)
#   bme280 = adafruit_bme280.Adafruit_BME280_SPI(spi, bme_cs)


# ----------------------------------------------------------------------------
#                              C O N F I G U R E
# ----------------------------------------------------------------------------

# change this to match the location's pressure (hPa) at sea level
if not bDebug :
    bme680.sea_level_pressure = 1013.25

# Print some info along the way
bVerbose = True

# Subtract this value from reported temperature
temp_corr = 2.30

# Height at installation  location
height_at_location = 412.0

# MQTT broker
host="192.168.1.7"

# MQTT broker port
port=1883

# Username to login at server
user="vscp"

# Password to login at server
password="secret"

# Sensor index for sensors (BME680)
# Default is to use GUID to identify sensor
sensorindex_temperature = 0
sensorindex_humidity = 0
sensorindex_pressure = 0
sensorindex_pressure_adj = 0
sensorindex_gas = 0
sensorindex_altitude = 0

# Zone for module
zone=0

# Subzone for module
subzone=0

# Last two bytes for GUID is made up of number
# given here on the form MSB:LSB
id_temperature = 1
id_humidity = 2
id_pressure = 3
id_pressure_adj = 4
id_gas = 5
id_altitude = 6

# Configuration will be read from path set here
config=""   

# ----------------------------------------------------------------------------

args = sys.argv[1:]
nargs = len(args)

try:
    opts, args = getopt.getopt(args,"hvc:",["help","verbose","config="])
except getopt.GetoptError:
    print("unrecognized format!")
    usage()
    sys.exit(2)
for opt, arg in opts:
    if opt in ("-h", "--help"):
        print("HELP")
        usage()
        sys.exit()
    elif opt in ("-v", "--verbose"):
        bverbose = True
    elif opt in ("-c", "--config"):
        config = arg

# read config file if one is specified
if (len(config)):
    config.read(config)

# define message callback
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

# define connect callback
def on_connect(client, userdata, flags, rc):
    print("Connected =",str(rc))

    

client= mqtt.Client()

# bind callback function
client.on_message=on_connect
client.on_message=on_message

client.username_pw_set(user, password)

if bVerbose :
    print("\n\nConnection in progress...", host)
client.connect(host,port)    

client.loop_start()     # start loop to process received messages

# raise ValueError('Unable to open vscphelp library session')

if bVerbose :
    print("-------------------------------------------------------------------------------")
    print("Sending...")

# -----------------------------------------------------------------------------
#                           T E M P E R A T U R E
# -----------------------------------------------------------------------------

if not bDebug :
    temperature = "%0.1f".format(bme680.temperature - temp_corr)
else:     
    temperature = "-27.8"    

if bVerbose :
    print("Temperature:", temperature, "C")

ex = vscp.vscpEventEx()
initEvent(ex,id_temperature, vc.VSCP_CLASS2_MEASUREMENT_STR,vt.VSCP_TYPE_MEASUREMENT_TEMPERATURE)

# Size is predata + string length + terminating zero
ex.sizedata = 4 + len(temperature) + 1
ex.data[0] = sensorindex_temperature
ex.data[1] = zone
ex.data[2] = subzone
ex.data[3] = 1  # unit is degrees Celsius
b = temperature.encode()
for idx in range(len(b)):
    ex.data[idx + 4] = b[idx]
ex.data[4 + len(temperature)] = 0  # optional terminating zero

client.publish("house/temperature",temperature)
# rv = vscphelper.sendEventEx(h1,ex)
# if vscp.VSCP_ERROR_SUCCESS != rv :
#     vscphelper.closeSession(h1)
#     raise ValueError('Command error: sendEventEx  Error code=%d' % rv )

# -----------------------------------------------------------------------------
#                             H U M I D I T Y
# -----------------------------------------------------------------------------

if not bDebug :
    humidity = "%0.1f".format(bme680.humidity)
else:     
    humidity = "1.23"

if bVerbose :
    print("Humidity:",humidity,"%")

ex = vscp.vscpEventEx()
initEvent(ex, id_humidity, vc.VSCP_CLASS2_MEASUREMENT_STR,vt.VSCP_TYPE_MEASUREMENT_HUMIDITY)

# Size is predata + string length + terminating zero
ex.sizedata = 4 + len(humidity) + 1
ex.data[0] = sensorindex_humidity
ex.data[1] = zone
ex.data[2] = subzone
ex.data[3] = 0  # default unit % of moisture
b = humidity.encode()
for idx in range(len(b)):
    ex.data[idx + 4] = b[idx]
ex.data[4 + len(humidity)] = 0  # optional terminating zero

client.publish("house/humidity",humidity)
# rv = vscphelper.sendEventEx(h1,ex)
# if vscp.VSCP_ERROR_SUCCESS != rv :
#     vscphelper.closeSession(h1)
#     raise ValueError('Command error: sendEventEx  Error code=%d' % rv )

# -----------------------------------------------------------------------------
#                             P R E S S U R E
# -----------------------------------------------------------------------------

if not bDebug :
    pressure = "%0.3f".format(bme680.pressure*100)
else:     
    pressure = "102300"

if bVerbose :
    print("Pressure:", pressure, "Pa")

ex = vscp.vscpEventEx()
initEvent(ex, id_pressure, vc.VSCP_CLASS2_MEASUREMENT_STR,vt.VSCP_TYPE_MEASUREMENT_PRESSURE)

# Size is predata + string length + terminating zero
ex.sizedata = 4 + len(pressure) + 1
ex.data[0] = sensorindex_pressure
ex.data[1] = zone
ex.data[2] = subzone
ex.data[3] = 0  # default unit Pascal
b = pressure.encode()
for idx in range(len(b)):
    ex.data[idx + 4] = b[idx]
ex.data[4 + len(pressure)] = 0  # optional terminating zero

client.publish("house/pressure",pressure)
# rv = vscphelper.sendEventEx(h1,ex)
# if vscp.VSCP_ERROR_SUCCESS != rv :
#     vscphelper.closeSession(h1)
#     raise ValueError('Command error: sendEventEx  Error code=%d' % rv )

# -----------------------------------------------------------------------------
#                           Adjusted Pressure
# -----------------------------------------------------------------------------

if not bDebug :
    pressure = "%0.3f".format((bme680.pressure + height_at_location/8.3)*100)
else:     
    pressure = "1000"   

if bVerbose :
    print("Relative pressure:", pressure, "Pa")

ex = vscp.vscpEventEx()
initEvent(ex, id_pressure_adj, vc.VSCP_CLASS2_MEASUREMENT_STR,vt.VSCP_TYPE_MEASUREMENT_PRESSURE)

# Size is predata + string length + terminating zero
ex.sizedata = 4 + len(pressure) + 1
ex.data[0] = sensorindex_pressure_adj
ex.data[1] = zone
ex.data[2] = subzone
ex.data[3] = 0  # default unit Pascal
b = pressure.encode()
for idx in range(len(b)):
    ex.data[idx + 4] = b[idx]
ex.data[4 + len(pressure)] = 0  # optional terminating zero

client.publish("house/relpressure",pressure)
# rv = vscphelper.sendEventEx(h1,ex)
# if vscp.VSCP_ERROR_SUCCESS != rv :
#     vscphelper.closeSession(h1)
#     raise ValueError('Command error: sendEventEx  Error code=%d' % rv )

# -----------------------------------------------------------------------------
#                                   Gas
# -----------------------------------------------------------------------------

if not bDebug :
    gas = "%d".format(bme680.gas)
else:     
    gas = "150000"   

if bVerbose :
    print("Gas:",gas,"Ohm")

ex = vscp.vscpEventEx()
initEvent(ex, id_gas, vc.VSCP_CLASS2_MEASUREMENT_STR,vt.VSCP_TYPE_MEASUREMENT_ELECTRICAL_RESISTANCE)

# Size is predata + string length + terminating zero
ex.sizedata = 4 + len(gas) + 1
ex.data[0] = sensorindex_gas
ex.data[1] = zone
ex.data[2] = subzone
ex.data[3] = 0  # default unit Ohms
b = gas.encode()
for idx in range(len(b)):
    ex.data[idx + 4] = b[idx]
ex.data[4 + len(gas)] = 0  # optional terminating zero

client.publish("house/gas",gas)
# rv = vscphelper.sendEventEx(h1,ex)
# if vscp.VSCP_ERROR_SUCCESS != rv :
#     vscphelper.closeSession(h1)
#     raise ValueError('Command error: sendEventEx  Error code=%d' % rv )

# -----------------------------------------------------------------------------
#                                Altitude
# -----------------------------------------------------------------------------

if not bDebug :
    altitude = "%0.2f".format(bme680.altitude)
else:     
    altitude = "420"    

if bVerbose :
    print("Altitude",altitude,"meter")

ex = vscp.vscpEventEx()
initEvent(ex, id_altitude, vc.VSCP_CLASS2_MEASUREMENT_STR,vt.VSCP_TYPE_MEASUREMENT_ALTITUDE)

# Size is predata + string length + terminating zero
ex.sizedata = 4 + len(altitude) + 1
ex.data[0] = sensorindex_altitude
ex.data[1] = zone
ex.data[2] = subzone
ex.data[3] = 0  # default unit Meters
b = altitude.encode()
for idx in range(len(b)):
    ex.data[idx + 4] = b[idx]
ex.data[4 + len(altitude)] = 0  # optional terminating zero

client.publish("house/altitude",altitude)
# rv = vscphelper.sendEventEx(h1,ex)
# if vscp.VSCP_ERROR_SUCCESS != rv :
#     vscphelper.closeSession(h1)
#     raise ValueError('Command error: sendEventEx  Error code=%d' % rv )


client.disconnect() 
client.loop_stop() 

if bVerbose :
    print("-------------------------------------------------------------------------------")
    print("Closed")
