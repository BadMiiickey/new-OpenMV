from pyb import UART # type: ignore
from pid import PID # type: ignore

class MotorHandler:
    UART3 = UART(3, 115200)
    
    CRUISE_SPEED: int = 180 # 巡航速度
    BRAKE_DISTANCE: int = 480 # 刹车区域距离(单位mm)

    # 转向PID参数
    xPid = PID(0.17, 0, 0.1)

    @classmethod
    def motorInit(cls):
        '''初始化推进器'''
        cls.UART3.init(115200, 8, None, 1)

    @staticmethod
    def linearMap(x: float | int, inMin: float | int, inMax: float | int, outMin: float | int, outMax: float | int):
        '''线性映射'''
        accurateValue = (x - inMin) * (outMax - outMin) / (inMax - inMin) + outMin
        approximateValue = int(100 * round(accurateValue, 2)) # 保留2位小数

        return approximateValue
    
