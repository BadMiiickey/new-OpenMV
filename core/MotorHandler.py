from pyb import UART # type: ignore
from pid import PID # type: ignore

class MotorHandler:
    __UART3 = UART(3, 115200)
    __CRUISE_SPEED: int = 190 # 巡航速度

    __xPid = PID(0.22, 0, 0) # 转向PID参数

    @classmethod
    def motorInit(cls) -> None:
        '''初始化推进器'''
        cls.__UART3.init(115200, 8, None, 1)

    @classmethod
    def getXOutput(cls, xError: float) -> float:
        '''根据x轴误差获取转向输出'''
        return cls.__xPid.get_pid(xError, 1)

    @classmethod
    def getHOutput(cls, distance: float) -> int:
        '''根据距离获取前进速度'''
        STOP_DISTANCE: int = 700 # 期望停下的距离(单位mm)
        BRAKE_SPEED: int = -80 # 停止时的速度(负值表示倒退)

        if (distance > STOP_DISTANCE or distance == float('inf')):
            return cls.__CRUISE_SPEED
        else:
            return BRAKE_SPEED

    @classmethod
    def getLeftOutput(cls, h: float, x: float) -> int:
        '''根据当前速度和转向输出获取左轮输出'''
        rawOut: float = max(-cls.__CRUISE_SPEED, min(500, h + x))
        left: float = cls.__linearMap(rawOut, -500, 500, 5, 10)

        return left
    
    @classmethod
    def getRightOutput(cls, h: float, x: float) -> int:
        '''根据当前速度和转向输出获取右轮输出'''
        rawOut: float = max(-cls.__CRUISE_SPEED, min(500, h - x))
        right: float = cls.__linearMap(rawOut, -500, 500, 5, 10)

        return right
    
    @classmethod
    def sendMotorCommand(cls, left: int, right: int) -> None:
        '''发送电机驱动占空比至STM32'''        
        command: str = f'A0B{left:03d}{right:03d}C'
        cls.__UART3.write(command)

    @classmethod
    def sendMaxConfidence(cls, value: float) -> None:
        '''发送属性至STM32'''
        valueInTenths: int = int(round(value * 100))
        valueInTenths = max(0, min(999, valueInTenths))

        cls.__UART3.write(f'A1Bconfidence!{valueInTenths:03d}C')

    @staticmethod
    def __linearMap(x: float, inMin: int, inMax: int, outMin: int, outMax: int) -> int:
        '''线性映射'''
        accurateValue: float = (x - inMin) * (outMax - outMin) / (inMax - inMin) + outMin
        approximateValue: int = int(100 * round(accurateValue, 2)) # 保留2位小数

        return approximateValue
