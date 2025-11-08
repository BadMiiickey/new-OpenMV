from pyb import LED # type: ignore

class LEDHandler:
    LED_TARGET_CONFIG: dict[int, LED] = {
        1: LED(2), # 绿色
        2: LED(1), # 红色
        3: LED(3) # 黄色
    }

    @classmethod
    def toggleLED(cls, ledId: int) -> None:
        '''LED闪烁'''
        LED(ledId).toggle()

    @classmethod
    def showCurrentTarget(cls, currentTarget: int) -> None:
        '''通过LED显示当前识别目标'''
        if (currentTarget not in cls.LED_TARGET_CONFIG): return None

        for key in cls.LED_TARGET_CONFIG:
            if (key == currentTarget):
                cls.LED_TARGET_CONFIG[key].on()
            else:
                cls.LED_TARGET_CONFIG[key].off()
