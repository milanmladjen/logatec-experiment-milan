import Adafruit_BBIO.GPIO as GPIO
import time

# Hold device in the reset state (until it is flashed again)
GPIO.setup("GPIO1_25", GPIO.OUT)
GPIO.output("GPIO1_25", GPIO.LOW)
time.sleep(2)
GPIO.output("GPIO1_25", GPIO.HIGH)