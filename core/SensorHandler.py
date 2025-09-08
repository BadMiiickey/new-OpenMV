import time # type:ignore

from core.MVHandler import MVHandler

from pyb import UART # type: ignore

class SensorHandler:
    UART1 = UART(1, 921600)  # P0(RX), P1(TX)
    buffer = bytearray()  # 用于存储接收到的数据

    minValidDistance: int = 100  # 最小有效距离, 小于此值则认为测量无效
    touchValidDistance: int = 200  # 有效触碰距离, 小于此值则认为是触碰
    touchCount: int = 0 # 触碰计数, 排除异常数据的干扰

    # 初始化激光传感器
    @classmethod
    def sensorInit(cls):
        cls.UART1.init(921600, 8, None, 1)
        time.sleep(2)

    # 读取一帧数据, 返回完整的47字节数据, 帧头为0x54
    @classmethod
    def readFrame(cls):
        cls.buffer += cls.UART1.read(cls.UART1.any()) if (cls.UART1.any()) else bytearray()

        while (len(cls.buffer) >= 47):
            if (cls.buffer[0] == 0x54):
                frame = cls.buffer[:47]
                cls.buffer = cls.buffer[47:]

                return frame
            else:
                cls.buffer = cls.buffer[1:]
        return None

    # 更新触碰计数
    @classmethod
    def updateTouchCount(cls, data):
        if (cls.__getClosestDistance(data) <= cls.touchValidDistance):
            cls.touchCount += 1
        else:
            cls.touchCount = 0

        # 连续3次均小于200mm则认为是有效数据
        if (cls.touchCount >= 3):
            cls.touchCount = 0
            MVHandler.currentTarget += 1
            MVHandler.currentTarget = 1 if (MVHandler.currentTarget >= 4) else MVHandler.currentTarget
    
    # 获取最近的测量距离
    @classmethod
    def __getClosestDistance(cls, data):
        rawData = list(data)
        distanceList = []

        for i in range(6, len(rawData) - 2, 3):
            if (i + 1 >= len(rawData)): continue

            distance = rawData[i] + (rawData[i + 1] << 8)
            
            distanceList.append(distance)

        return min(distanceList) if (distanceList) else float('inf')