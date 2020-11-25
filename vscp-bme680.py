#!/usr/bin/env python

################################################################################
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

import sys
import configparser
import getopt

import vscp
import vscp_class as vc
import vscp_type as vt
import vscphelper

import time

# Set to True to run with simulated data
bDebug = True

config = configparser.ConfigParser()

if not bDebug :
    import board
    import busio
    import adafruit_bme680

def usage():
    print("usage: vscp-bm680.py -v -c <pat-to-config-file> -h ")
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
    return g


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
bVerbose = False

# Subtract this value from reported temperature
temp_corr = 2.30

# Height at installation  location
height_at_location = 412.0

# Server and port
host="192.168.1.7:9598"

# Username to login at server
user="admin"

# Password to login at server
password="secret"

# GUID for sensors (Ethernet MAC used if empty)
# Should normally have two LSB's set to zero for sensor id use
guid=""

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
cfgpath=""  

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
        bVerbose = True
    elif opt in ("-c", "--config"):
        cfgpath = arg

# read config file if one is specified

if (len(cfgpath)):
    init = config.read(cfgpath)
    if 'bVerbose' in config['GENERAL']:
        bVerbose = config.getboolean('GENERAL','bVerbose')
        if bVerbose :
            print('Verbose mode enabled.')
            print('READING CONFIGURATION')
            print('---------------------')
    if 'host' in config['VSCP']:        
        host = config['VSCP']['host']
        if bVerbose:
            print("host =", host)
    if 'user' in config['VSCP']:        
        user = config['VSCP']['user']
        if bVerbose:
            print("user =", user)
    
    if 'password' in config['VSCP']:        
        password = config['VSCP']['password']
        if bVerbose:
            print("password =", "***********")
            print("password =", password)

    if 'guid' in config['VSCP']:        
        guid = config['VSCP']['guid']
        if bVerbose:
            print("guid =", guid)
    
    if 'sensorindex_temperature' in config['VSCP']:        
        sensorindex_temperature = int(config['VSCP']['sensorindex_temperature'])
        if bVerbose:
            print("sensorindex_temperature =", sensorindex_temperature)

    if 'sensorindex_humidity' in config['VSCP']:        
        sensorindex_humidity = int(config['VSCP']['sensorindex_humidity'])
        if bVerbose:
            print("sensorindex_humidity =", sensorindex_humidity)
    
    if 'sensorindex_pressure' in config['VSCP']:        
        sensorindex_pressure = int(config['VSCP']['sensorindex_pressure'])
        if bVerbose:
            print("sensorindex_pressure =", sensorindex_pressure)
    
    if 'sensorindex_pressure_adj' in config['VSCP']:        
        sensorindex_pressure_adj = int(config['VSCP']['sensorindex_pressure_adj'])
        if bVerbose:
            print("sensorindex_pressure_adj =", sensorindex_pressure_adj)
    
    if 'sensorindex_gas' in config['VSCP']:        
        sensorindex_gas = int(config['VSCP']['sensorindex_gas'])
        if bVerbose:
            print("sensorindex_gas =", sensorindex_gas)
    
    if 'sensorindex_altitude' in config['VSCP']:        
        sensorindex_altitude = int(config['VSCP']['sensorindex_altitude'])
        if bVerbose:
            print("sensorindex_altitude =", sensorindex_altitude)

    if 'zone' in config['VSCP']:        
        zone = int(config['VSCP']['zone'])
        if bVerbose:
            print("zone =", zone)

    if 'subzone' in config['VSCP']:        
        subzone = int(config['VSCP']['subzone'])
        if bVerbose:
            print("subzone =", subzone)
    
    if 'id_temperature' in config['VSCP']:        
        id_temperature = int(config['VSCP']['id_temperature'])
        if bVerbose:
            print("id_temperature =", id_temperature)
    
    if 'id_humidity' in config['VSCP']:        
        id_humidity = int(config['VSCP']['id_humidity'])
        if bVerbose:
            print("id_humidity =", id_humidity)
    
    if 'id_pressure' in config['VSCP']:        
        id_pressure = int(config['VSCP']['id_pressure'])
        if bVerbose:
            print("id_pressure =", id_pressure)
    
    if 'id_pressure_adj' in config['VSCP']:        
        id_pressure_adj = int(config['VSCP']['id_pressure_adj'])
        if bVerbose:
            print("id_pressure_adj =", id_pressure_adj)
    
    if 'id_gas' in config['VSCP']:        
        id_gas = int(config['VSCP']['id_gas'])
        if bVerbose:
            print("id_gas =", id_gas)
    
    if 'id_altitude' in config['VSCP']:        
        id_altitude = int(config['VSCP']['id_altitude'])
        if bVerbose:
            print("id_altitude =", id_altitude)

    if 'sea_level_pressure' in config['BME680']:
        if not bDebug :
            bme680.sea_level_pressure = float(config['BME680']['sea_level_pressure'])       
        if bVerbose:
            print("bme6880.sea_level_pressure =", float(config['BME680']['sea_level_pressure']))
    
    if 'temp_corr' in config['BME680']:
        if not bDebug :
            temp_corr = float(config['BME680']['temp_corr'])       
        if bVerbose:
            print("temp_corr =", temp_corr)
    
    if 'height_at_location' in config['BME680']:
        if not bDebug :
            height_at_location = float(config['BME680']['height_at_location'])       
        if bVerbose:
            print("height_at_location =", temp_corr)

# -----------------------------------------------------------------------------
    
h1 = vscphelper.newSession()
if (0 == h1 ):
    vscphelper.closeSession(h1)
    raise ValueError('Unable to open vscphelp library session')

if bVerbose :
    print("\n\nConnection in progress...")

rv = vscphelper.open(h1,host,user,password)
if vscp.VSCP_ERROR_SUCCESS == rv :
    if bVerbose :
        print("Connected")
else:
    vscphelper.closeSession(h1)
    raise ValueError('Command error: open on channel 1  Error code=%d' % rv )

if bVerbose :
    print("-------------------------------------------------------------------------------")
    print("Sending...")

# -----------------------------------------------------------------------------
#                           T E M P E R A T U R E
# -----------------------------------------------------------------------------

if not bDebug :
    temperature = "{:0.1f}".format(bme680.temperature - temp_corr)
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

rv = vscphelper.sendEventEx(h1,ex)
if vscp.VSCP_ERROR_SUCCESS != rv :
    vscphelper.closeSession(h1)
    raise ValueError('Command error: sendEventEx  Error code=%d' % rv )

# -----------------------------------------------------------------------------
#                             H U M I D I T Y
# -----------------------------------------------------------------------------

if not bDebug :
    humidity = "{:0.1f}".format(bme680.humidity)
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

rv = vscphelper.sendEventEx(h1,ex)
if vscp.VSCP_ERROR_SUCCESS != rv :
    vscphelper.closeSession(h1)
    raise ValueError('Command error: sendEventEx  Error code=%d' % rv )

# -----------------------------------------------------------------------------
#                             P R E S S U R E
# -----------------------------------------------------------------------------

if not bDebug :
    pressure = "{:0.0f}".format(bme680.pressure*100)
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

rv = vscphelper.sendEventEx(h1,ex)
if vscp.VSCP_ERROR_SUCCESS != rv :
    vscphelper.closeSession(h1)
    raise ValueError('Command error: sendEventEx  Error code=%d' % rv )

# -----------------------------------------------------------------------------
#                           Adjusted Pressure
# -----------------------------------------------------------------------------

if not bDebug :
    pressure = "{:0.0f}".format((bme680.pressure + height_at_location/8.3)*100)
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

rv = vscphelper.sendEventEx(h1,ex)
if vscp.VSCP_ERROR_SUCCESS != rv :
    vscphelper.closeSession(h1)
    raise ValueError('Command error: sendEventEx  Error code=%d' % rv )

# -----------------------------------------------------------------------------
#                                   Gas
# -----------------------------------------------------------------------------

if not bDebug :
    gas = "{:d}".format(bme680.gas)
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

rv = vscphelper.sendEventEx(h1,ex)
if vscp.VSCP_ERROR_SUCCESS != rv :
    vscphelper.closeSession(h1)
    raise ValueError('Command error: sendEventEx  Error code=%d' % rv )

# -----------------------------------------------------------------------------
#                                Altitude
# -----------------------------------------------------------------------------

if not bDebug :
    altitude = "{:0.1f}".format(bme680.altitude)
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

rv = vscphelper.sendEventEx(h1,ex)
if vscp.VSCP_ERROR_SUCCESS != rv :
    vscphelper.closeSession(h1)
    raise ValueError('Command error: sendEventEx  Error code=%d' % rv )


rv = vscphelper.close(h1)
if vscp.VSCP_ERROR_SUCCESS != rv :
    vscphelper.closeSession(h1)
    raise ValueError('Command error: close  Error code=%d' % rv )

vscphelper.closeSession(h1)

if bVerbose :
    print("-------------------------------------------------------------------------------")
    print("Closed")