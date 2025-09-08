from pyb import UART # type: ignore

class MotorHandler:
    UART3 = UART(3, 115200)

    # 是否自动控制
    isAutoControl: bool = True

    # 手动控制速度
    leftCtrl: int | float | None = None
    rightCtrl: int | float | None = None

    # 自动控制相关变量
    leftOut: int | float | None = None
    rightOut: int | float | None = None
    mappedA: int | float | None = None
    mappedB: int | float | None = None
    # hasOffset: bool = False # 是否抵消惯性

    # 初始化电机
    @classmethod
    def motorInit(cls):
        cls.UART3.init(115200, 8, None, 1)

    # 线性映射
    @staticmethod
    def linearMap(x: float | int, inMin: float | int, inMax: float | int, outMin: float | int, outMax: float | int):
        accurateValue = (x - inMin) * (outMax - outMin) / (inMax - inMin) + outMin
        approximateValue = 100 * round(accurateValue, 2) # 保留2位小数
        
        return approximateValue