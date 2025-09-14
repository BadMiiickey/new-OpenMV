from pyb import LED # type: ignore

class LEDHandler:
    LED_TARGET_CONFIG = {
        1: LED(2), # 绿色
        2: LED(1), # 红色
        3: LED(3) # 黄色
    }

    # LED闪烁
    @classmethod
    def toggleLED(cls, ledId: int):
        '''LED闪烁'''
        LED(ledId).toggle()

    # 通过LED显示当前识别目标
    @classmethod
    def showCurrentTarget(cls, currentTarget: int):
        '''通过LED显示当前识别目标'''
        if (currentTarget not in cls.LED_TARGET_CONFIG): return None

        for key in cls.LED_TARGET_CONFIG:
            if (key == currentTarget):
                cls.LED_TARGET_CONFIG[key].on()
            else:
                cls.LED_TARGET_CONFIG[key].off()
