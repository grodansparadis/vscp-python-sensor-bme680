# vscp-python-sensor-bme680

![License](https://img.shields.io/badge/license-MIT-blue.svg)

<img src="https://vscp.org/images/logo.png" width="100">

VSCP routines to deliver data from BME680 sensor to a VSCP daemon or a MQTT broker. It is built upon the [Adafruit BME680 module](https://github.com/adafruit/Adafruit_CircuitPython_BME680)

It will deliver VSCP events for

* Temperature
* Humidity
* Pressure (raw reading)
* Pressure (adjusted for sea level)
* Altitude
* Gas concentration

Typically used in a cron job to deliver the events on timed intervals.

## Install

The script depends on some other modules that you need to install before using it.

### Install adafruit-circuitpython-bme680 module
On supported GNU/Linux systems like the Raspberry Pi, you can install the driver locally from PyPI. To install for current user:

```bash
pip3 install adafruit-circuitpython-bme680
```

To install system-wide (this may be required in some cases):

```bash
sudo pip3 install adafruit-circuitpython-bme680
```

To install in a virtual environment in your current project:

```bash
mkdir project-name && cd project-name
python3 -m venv .env
source .env/bin/activate
pip3 install adafruit-circuitpython-bme680
```

### Install VSCP modules

**pyvscphelper** is not needed if only MQTT should be used. You can install the modules from PyPi

```bash
pip3 install pyvscp
pip3 install pyvscphelper
pip3 install pyvscpclasses
pip3 install pyvscptypes
```

If you need them on more places either go for a global install or use a virtual environment and install all the modules in it.

### Install MQTT module

For MQTT functionality Paho MQTT module is needed. You can install the modules from PyPi

```bash
pip3 install paho-mqtt
```

## Install

You setup the code by editing the script. All relevant values are in the beginning of the file. Documentation is in the file.


----

If you are intrested in learning more about VSCP the main site is [here](https://www.vscp.org)

Copyright © 2000-2020 Ake Hedman, Grodans Paradis AB - MIT license.

