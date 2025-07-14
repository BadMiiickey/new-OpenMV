import pyb #type:ignore

class TimeHelper:

    #获取当前时间
    @staticmethod
    def getCurrentTime() -> int:
        return pyb.millis()
    
    #延时函数, 在指定的毫秒数内执行指定的函数
    @classmethod
    def delayWithStartAction(cls, durationMs: int, action):
        startTime = cls.getCurrentTime()

        while (cls.getCurrentTime() - startTime < durationMs):
            action()