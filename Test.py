import time

from pyb import LED #type:ignore

led = LED(2)

while(True):
    led.toggle()
    time.sleep(0.5)