from Helper.MVHelper import MVHelper
from Helper.MotorHelper import MotorHelper

class PrintHelper:
    actions = {
        1: lambda: (
            print('leftCtrl:', MotorHelper.leftCtrl),
            print('rightCtrl:', MotorHelper.rightCtrl)
        ),
        2: lambda: (
            print("leftOut:", MotorHelper.leftOut),
            print("rightOut:", MotorHelper.rightOut)
        ),
        3: lambda: (
            print("mappedA:", MotorHelper.mappedA),
            print("mappedB:", MotorHelper.mappedB)
        ),
        4: lambda: (
            print("Left Pulse Width:", MotorHelper.leftPulseWith),
            print("Right Pulse Width:", MotorHelper.rightPulseWith)
        ),
        5: lambda: (
            print("Current Brightness:", MVHelper.currentBrightness),
            print("Current Exposure:", MVHelper.currentExposure)
        )
    }
    
    @classmethod
    def messagePrint(cls, case: int):
        action = cls.actions.get(case, lambda: print("Invalid case"))
        action()