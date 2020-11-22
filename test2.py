import time
     
import board
import busio
import adafruit_bme680
     
# Create library object using our Bus I2C port
i2c = busio.I2C(board.SCL, board.SDA)
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c)
     
# OR create library object using our Bus SPI port
# spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
# bme_cs = digitalio.DigitalInOut(board.D10)
# bme280 = adafruit_bme280.Adafruit_BME280_SPI(spi, bme_cs)
     
# change this to match the location's pressure (hPa) at sea level
bme680.sea_level_pressure = 1013.25
temp_corr = 2.30
height_at_location = 412.0
     
while True:
    print("\nTemperature: %0.1f C" % (bme680.temperature - temp_corr))
    print("Humidity: %0.1f %%" % bme680.humidity)
    print("Pressure: %0.1f hPa" % bme680.pressure)
    print("Altitude = %0.2f meters" % bme680.altitude)
    print("Relative pressure = %0.3f hPa" % (bme680.pressure + height_at_location/8.3))
    print("Relative pressure = %0.3f hPa" % (((bme680.pressure)/pow((1-((float)(height_at_location))/44330), 5.255))))
    print("Relative calculated pressure = %0.3f hPa" % (((bme680.pressure)/pow((1-((float)(bme680.altitude))/44330), 5.255))))

    time.sleep(2)
