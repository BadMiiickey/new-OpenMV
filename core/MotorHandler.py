from pyb import UART # type: ignore
from pid import PID # type: ignore

class MotorHandler:
    UART3 = UART(3, 115200)
    
    CRUISE_SPEED: int = 180 # 巡航速度
    STOP_DISTANCE: int = 250 # 期望停下的距离(单位mm)

    BASE_SIZE: int = 400 # 基准目标像素面积
    MIN_SCALE: float = 0.3  # 近距离时，最小缩放为0.3倍，防止抖动
    MAX_SCALE: float = 1.2  # 远距离时，最大放大为1.2倍，增强转向

    # 转向PID参数
    xPid = PID(0.18, 0, 0)

    @classmethod
    def motorInit(cls) -> None:
        '''初始化推进器'''
        cls.UART3.init(115200, 8, None, 1)

    @classmethod
    def getXOutput(cls, xError: float, currentMaxSize: int) -> float:
        '''根据x轴误差获取转向输出'''
        pidOutput: float = cls.xPid.get_pid(xError, 1)
        scaleFactor: float = cls.BASE_SIZE / currentMaxSize if (currentMaxSize > 0) else cls.MAX_SCALE
        clampedScaleFactor: float = max(cls.MIN_SCALE, min(cls.MAX_SCALE, scaleFactor))

        return pidOutput * clampedScaleFactor

    @classmethod
    def getHOutput(cls, distance: float) -> int:
        '''根据距离获取前进速度'''
        if (distance > cls.STOP_DISTANCE):
            return cls.CRUISE_SPEED
        else:
            return -cls.CRUISE_SPEED - int((cls.STOP_DISTANCE - distance) * 0.5)
        
    @classmethod
    def getLeftOutput(cls, currentSpeed: float, x: float) -> int:
        '''根据当前速度和转向输出获取左轮输出'''
        rawOut: float = max(-cls.CRUISE_SPEED, min(500, currentSpeed + x))
        left: float = cls.__linearMap(rawOut, -500, 500, 5, 10)

        return left
    
    @classmethod
    def getRightOutput(cls, currentSpeed: float, x: float) -> int:
        '''根据当前速度和转向输出获取右轮输出'''
        rawOut: float = max(-cls.CRUISE_SPEED, min(500, currentSpeed - x))
        right: float = cls.__linearMap(rawOut, -500, 500, 5, 10)

        return right
    
    @classmethod
    def sendMotorCommand(cls, left: int, right: int) -> None:
        '''发送电机驱动占空比至STM32'''        
        command: str = f'A0B{left:03d}{right:03d}C'
        cls.UART3.write(command)

    @classmethod
    def sendMaxConfidence(cls, value: float) -> None:
        '''发送属性至STM32'''
        valueInTenths: int = int(round(value * 100))
        valueInTenths = max(0, min(999, valueInTenths))

        cls.UART3.write(f'A1Bconfidence!{valueInTenths:03d}C')

    @staticmethod
    def __linearMap(x: float, inMin: int, inMax: int, outMin: int, outMax: int) -> int:
        '''线性映射'''
        accurateValue: float = (x - inMin) * (outMax - outMin) / (inMax - inMin) + outMin
        approximateValue: int = int(100 * round(accurateValue, 2)) # 保留2位小数

        return approximateValue
