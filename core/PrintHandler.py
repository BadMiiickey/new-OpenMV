from core.MVHandler import MVHandler
from core.MotorHandler import MotorHandler
from core.SensorHandler import SensorHandler

class PrintHandler:
    actions = {
        1: lambda: (
            print('leftCtrl:', MotorHandler.leftCtrl),
            print('rightCtrl:', MotorHandler.rightCtrl)
        ),
        2: lambda: (
            print('leftOut:', MotorHandler.leftOut),
            print('rightOut:', MotorHandler.rightOut)
        ),
        3: lambda: (
            print('mappedA:', MotorHandler.mappedA),
            print('mappedB:', MotorHandler.mappedB)
        ),
        5: lambda: (
            print('Current Brightness:', MVHandler.currentBrightness),
            print('Current Exposure:', MVHandler.currentExposure)
        )
    }
    
    @classmethod
    def messagePrint(cls, case: int):
        action = cls.actions.get(case, lambda: print('Invalid case'))
        action()