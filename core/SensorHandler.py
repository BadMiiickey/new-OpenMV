import time # type:ignore

from core.MVHandler import MVHandler

from pyb import UART # type: ignore

class SensorHandler:
    UART1 = UART(1, 921600)  # P0(RX), P1(TX)
    buffer = bytearray()  # 用于存储接收到的数据

    minValidDistance: int = 100  # 最小有效距离, 小于此值则认为测量无效
    touchValidDistance: int = 140  # 有效触碰距离, 小于此值则认为是触碰
    touchCount: int = 0 # 触碰计数, 排除异常数据的干扰

    # 初始化激光传感器
    @classmethod
    def sensorInit(cls):
        cls.UART1.init(921600, 8, None, 1)
        time.sleep(2)

    # 获取最近的测量距离
    @classmethod
    def getClosestDistance(cls, data):
        rawData = list(data)
        distanceList = []

        for i in range(6, len(rawData) - 2, 3):
            if (i + 1 >= len(rawData)): continue

            distance = rawData[i] + (rawData[i + 1] << 8)
            
            distanceList.append(distance)

        return min(distanceList) if (distanceList) else float('inf')

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
    @staticmethod
    def updateTouchCount(data):
        if (SensorHandler.getClosestDistance(data) <= SensorHandler.touchValidDistance):
            SensorHandler.touchCount += 1
        else:
            SensorHandler.touchCount = 0

        # 连续5次均小于140mm则认为是有效数据
        if (SensorHandler.touchCount >= 5):
            SensorHandler.touchCount = 0
            MVHandler.currentTarget += 1
            MVHandler.currentTarget = 1 if (MVHandler.currentTarget >= 4) else MVHandler.currentTarget