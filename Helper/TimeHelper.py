import pyb

class TimeHelper:

    @staticmethod
    def getCurrentTime():
        return pyb.millis()
    
    @staticmethod
    def delayWithStartAction(durationMs: int, action):
        startTime = TimeHelper.getCurrentTime()

        while (TimeHelper.getCurrentTime() - startTime < durationMs):
            action()
