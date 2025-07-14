import time 

from pyb import LED #type:ignore

class AssistantHelper:
    
    @staticmethod
    def mapValue(x: float | int, inMin: float | int, inMax: float | int, outMin: float | int, outMax: float | int):
        return (x - inMin) * (outMax - outMin) / (inMax - inMin) + outMin
    
    #LED闪烁
    @staticmethod
    def toggleLED(ledNumber: int, delay: float | int):
        led = LED(ledNumber) 

        led.toggle()
        time.sleep(delay)

    #通过LED显示当前识别目标
    @staticmethod
    def showCurrentTarget(ledNumber: int):
        led = LED(ledNumber)
        led.on()