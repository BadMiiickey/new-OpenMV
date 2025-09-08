import time 

from pyb import LED # type: ignore

class LEDHandler:

    # LED闪烁
    @staticmethod
    def toggleLED(ledNumber: int, delay: float | int):
        led = LED(ledNumber) 

        led.toggle()
        time.sleep(delay)

    # 通过LED显示当前识别目标
    @staticmethod
    def showCurrentTarget(ledNumber: int):
        led = LED(ledNumber)
        led.on()