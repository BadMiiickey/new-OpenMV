import time 

from pyb import LED #type:ignore

class AssistantHelper:
    
    @staticmethod
    def mapValue(x: float | int, inMin: float | int, inMax: float | int, outMin: float | int, outMax: float | int):
        return (x - inMin) * (outMax - outMin) / (inMax - inMin) + outMin
    
    @staticmethod
    def toggleLED(ledNumber: int, delay: float | int):
        led = LED(ledNumber)

        led.toggle()
        time.sleep(delay)