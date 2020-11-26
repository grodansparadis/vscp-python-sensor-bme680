#!/usr/bin/env python

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

import vscp
import vscp_class as vc
import vscp_type as vt
import vscphelper as vhlp

import json
import paho.mqtt.client as mqtt

import math
import time

# Set to True to run with simulated data
bDebug = True

# Set to True to use SPI instead of I2C
bUseSPI = False

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

# ----------------------------------------------------------------------------
#                              C O N F I G U R E
# ----------------------------------------------------------------------------

# change this to match the location's pressure (hPa) at sea level
sea_level_pressure = 1013.25

# Print some info along the way
bVerbose = False

# Subtract this value from reported temperature
temp_corr = 2.30

# Height at installation  location
height_at_location = 412.0

# GUID for sensors (Ethernet MAC used if empty)
# Should normally have two LSB's set to zero for sensor id use
guid=""

# MQTT broker
host="192.168.1.7"

# MQTT broker port
port=1883

# Username to login at server
user="vscp"

# Password to login at server
password="secret"

# MQTT publish topic. 
#   %guid% is replaced with GUID
#   %class% is replaced with event class
#   %type% is replaced with event type   
topic="vscp/{xguid}/miso/{xclass}/{xtype}"

# Sensor index for sensors (BME680)
# Default is to use GUID to identify sensor
sensorindex_temperature = 0
sensorindex_humidity = 0
sensorindex_pressure = 0
sensorindex_pressure_adj = 0
sensorindex_gas = 0
sensorindex_altitude = 0
sensorindex_dewpoint = 0

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
id_dewpoint = 7

note_temperature = "Temperature from BME680"
note_humidity = "Humidity from BME680"
note_pressure = "Pressure from BME680"
note_pressure_adj = "Sea level pressure from BME680"
note_gas = "Gas concentration from BME680"
note_altitude = "Altitude from BME680"
note_dewpoint = "Dewpoint from BME680"

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

if (len(cfgpath)):

    init = config.read(cfgpath)

    # ----------------- GENERAL -----------------
    if 'bVerbose' in config['GENERAL']:
        bVerbose = config.getboolean('GENERAL','bVerbose')
        if bVerbose :
            print('Verbose mode enabled.')
            print('READING CONFIGURATION')
            print('---------------------')    

    # ----------------- VSCP -----------------
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

    if 'sensorindex_dewpoint' in config['VSCP']:        
        sensorindex_dewpoint = int(config['VSCP']['sensorindex_dewpoint'])
        if bVerbose:
            print("sensorindex_dewpoint =", sensorindex_dewpoint)
    
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
    
    if 'id_dewpoint' in config['VSCP']:        
        id_dewpoint = int(config['VSCP']['id_dewpoint'])
        if bVerbose:
            print("id_dewpoint =", id_altitude)
    
    # ----------------- MQTT -----------------
    if 'host' in config['MQTT']:        
        host = config['MQTT']['host']
        if bVerbose:
            print("host =", host)

    if 'port' in config['MQTT']:        
        port = int(config['MQTT']['port'])
        if bVerbose:
            print("port =", port)

    if 'user' in config['MQTT']:        
        user = config['MQTT']['user']
        if bVerbose:
            print("user =", user)
    
    if 'password' in config['MQTT']:        
        password = config['MQTT']['password']
        if bVerbose:
            print("password =", "***********")
            #print("password =", password)

    if 'topic' in config['MQTT']:        
        topic = config['MQTT']['topic']
        if bVerbose:
            print("topic =", password)
    
    if 'note_temperature' in config['MQTT']:        
        note_temperature = config['MQTT']['note_temperature']
        if bVerbose:
            print("note_temperature =", note_temperature)
    
    if 'note_humidity' in config['MQTT']:        
        note_humidity = config['MQTT']['note_humidity']
        if bVerbose:
            print("note_humidity =", note_humidity)
    
    if 'note_pressure' in config['MQTT']:        
        note_pressure = config['MQTT']['note_pressure']
        if bVerbose:
            print("note_pressure =", note_pressure)
    
    if 'note_pressure_adj' in config['MQTT']:        
        note_pressure_adj = config['MQTT']['note_pressure_adj']
        if bVerbose:
            print("note_pressure_adj =", note_pressure_adj)

    if 'note_gas' in config['MQTT']:        
        note_gas = config['MQTT']['note_gas']
        if bVerbose:
            print("note_gas =", note_gas)

    if 'note_altitude' in config['MQTT']:        
        note_altitude = config['MQTT']['note_altitude']
        if bVerbose:
            print("note_altitude =", note_altitude)
    
    if 'note_dewpoint' in config['MQTT']:        
        note_dewpoint = config['MQTT']['note_dewpoint']
        if bVerbose:
            print("note_dewpoint =", note_dewpoint)
    
    # ----------------- BME680 -----------------
    if 'sea_level_pressure' in config['BME680']:
        if not bDebug :
            sea_level_pressure = float(config['BME680']['sea_level_pressure'])       
        if bVerbose:
            print("sea_level_pressure =", float(config['BME680']['sea_level_pressure']))
    
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

# Initialize VSCP event content
def initEvent(ex,id,vscpClass,vscpType):
    # Dumb node, priority normal
    ex.head = vscp.VSCP_PRIORITY_NORMAL | vscp.VSCP_HEADER16_DUMB
    g = vscp.guid()
    if (len(guid)):
        g.setFromString(guid)
    else :    
        g.setGUIDFromMAC(id)
    ex.guid = g.guid
    ex.vscpclass = vscpClass
    ex.vscptype = vscpType
    return g

# -----------------------------------------------------------------------------

# Create library object using our Bus I2C port
if not bUseSPI :
    if not bDebug :
        i2c = busio.I2C(board.SCL, board.SDA)
        bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c)

else :     
    # OR create library object using our Bus SPI port
    if not bDebug :
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        bme_cs = digitalio.DigitalInOut(board.D10)
        bme280 = adafruit_bme280.Adafruit_BME280_SPI(spi, bme_cs)

# -----------------------------------------------------------------------------

# change this to match the location's pressure (hPa) at sea level
if not bDebug :
    bme680.sea_level_pressure = sea_level_pressure

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
g = initEvent(ex, id_temperature, vc.VSCP_CLASS2_MEASUREMENT_STR, vt.VSCP_TYPE_MEASUREMENT_TEMPERATURE)

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

rv,str = vhlp.convertEventExToJSON(ex)
j = json.loads(str)
j["vscpNote"] = note_temperature
# Add extra measurement information
j["measurement"] = { 
    "value" : float(temperature),
    "unit" : 1,
    "sensorindex" : sensorindex_temperature,
    "zone" : zone,
    "subzone" : subzone
}

ptopic = topic.format( xguid=g.getAsString(), xclass=ex.vscpclass, xtype=ex.vscptype)
client.publish(ptopic, json.dumps(j))


# -----------------------------------------------------------------------------
#                             H U M I D I T Y
# -----------------------------------------------------------------------------

if not bDebug :
    humidity = "{:0.1f}".format(bme680.humidity)
else:     
    humidity = "{:0.1f}".format(1.23)

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

rv,str = vhlp.convertEventExToJSON(ex)
j["vscpNote"] = note_humidity
# Add extra measurement information
j["measurement"] = { 
    "value" : float(humidity),
    "unit" : 0,
    "sensorindex" : sensorindex_humidity,
    "zone" : zone,
    "subzone" : subzone
}

ptopic = topic.format( xguid=g.getAsString(), xclass=ex.vscpclass, xtype=ex.vscptype)
client.publish(ptopic, json.dumps(j))

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

rv,str = vhlp.convertEventExToJSON(ex)
j["vscpNote"] = note_pressure
# Add extra pressure information
j["measurement"] = { 
    "value" : float(pressure),
    "unit" : 0,
    "sensorindex" : sensorindex_pressure,
    "zone" : zone,
    "subzone" : subzone
}

ptopic = topic.format( xguid=g.getAsString(), xclass=ex.vscpclass, xtype=ex.vscptype)
client.publish(ptopic, json.dumps(j))

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

rv,str = vhlp.convertEventExToJSON(ex)
j["vscpNote"] = note_pressure_adj
# Add extra pressure information
j["measurement"] = { 
    "value" : float(pressure),
    "unit" : 0,
    "sensorindex" : sensorindex_pressure_adj,
    "zone" : zone,
    "subzone" : subzone
}

ptopic = topic.format( xguid=g.getAsString(), xclass=ex.vscpclass, xtype=ex.vscptype)
client.publish(ptopic, json.dumps(j))

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

rv,str = vhlp.convertEventExToJSON(ex)
j["vscpNote"] = note_gas
# Add extra pressure information
j["measurement"] = { 
    "value" : int(gas),
    "unit" : 0,
    "sensorindex" : sensorindex_gas,
    "zone" : zone,
    "subzone" : subzone
}

ptopic = topic.format( xguid=g.getAsString(), xclass=ex.vscpclass, xtype=ex.vscptype)
client.publish(ptopic, json.dumps(j))


# -----------------------------------------------------------------------------
#                                Altitude
# -----------------------------------------------------------------------------

if not bDebug :
    altitude = "{:0.0f}".format(bme680.altitude)
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

rv,str = vhlp.convertEventExToJSON(ex)
j["vscpNote"] = note_altitude
# Add extra pressure information
j["measurement"] = { 
    "value" : float(altitude),
    "unit" : 0,
    "sensorindex" : sensorindex_altitude,
    "zone" : zone,
    "subzone" : subzone
}

ptopic = topic.format( xguid=g.getAsString(), xclass=ex.vscpclass, xtype=ex.vscptype)
client.publish(ptopic, json.dumps(j))


# -----------------------------------------------------------------------------
#                                Dew point
# -----------------------------------------------------------------------------
# https://en.wikipedia.org/wiki/Dew_point#Calculating_the_dew_point

b = 17.62
c = 243.12
if not bDebug :
    gamma = (b * bme680.temperature /(c + bme680.temperature)) + math.log(bme680.humidity / 100.0)
else:
    gamma = 1
    
dewpoint = (c * gamma) / (b - gamma)

if not bDebug :
    dew = "{:0.1f}".format(dewpoint)
else:     
    dew = "12"    

if bVerbose :
    print("Dew point",dew,"C")

ex = vscp.vscpEventEx()
initEvent(ex, id_dewpoint, vc.VSCP_CLASS2_MEASUREMENT_STR,vt.VSCP_TYPE_MEASUREMENT_DEWPOINT)

# Size is predata + string length + terminating zero
ex.sizedata = 4 + len(dew) + 1
ex.data[0] = sensorindex_dewpoint
ex.data[1] = zone
ex.data[2] = subzone
ex.data[3] = 0  # default unit Meters
b = altitude.encode()
for idx in range(len(b)):
    ex.data[idx + 4] = b[idx]
ex.data[4 + len(dew)] = 0  # optional terminating zero

rv,str = vhlp.convertEventExToJSON(ex)
j["vscpNote"] = note_dewpoint
# Add extra pressure information
j["measurement"] = { 
    "value" : float(dewpoint),
    "unit" : 0,
    "sensorindex" : sensorindex_dewpoint,
    "zone" : zone,
    "subzone" : subzone
}

ptopic = topic.format( xguid=g.getAsString(), xclass=ex.vscpclass, xtype=ex.vscptype)
client.publish(ptopic, json.dumps(j))

# -----------------------------------------------------------------------------


client.disconnect() 
client.loop_stop() 

if bVerbose :
    print("-------------------------------------------------------------------------------")
    print("Closed")
