import pyb # type: ignore

from core.MotorHandler import MotorHandler

class TimeHandler:
    lastTime = 0

    # 获取当前时间
    @staticmethod
    def getCurrentTime() -> int:
        return pyb.millis()

    # 自动控制逻辑中, 每次循环结束时更新lastTime
    @classmethod
    def updateLastTime(cls):
        cls.lastTime = cls.getCurrentTime() if (cls.getCurrentTime() - cls.lastTime > 2000) else cls.lastTime

    # 更新lastTime, 2s未进行手动控制时, 切换为自动控制
    @classmethod
    def updateLastTimeWhenNotAutoControl(cls, checkTimeMs: int = 2000):
        if (cls.getCurrentTime() - cls.lastTime > 2000):
            cls.lastTime = cls.getCurrentTime()
            MotorHandler.isAutoControl = True