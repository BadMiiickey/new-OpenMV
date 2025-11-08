from pyb import UART # type: ignore

class SensorHandler:
    UART1 = UART(1, 921600) # P0(RX), P1(TX)

    FRAME_HEADER: bytes = b'\x54' # 帧头
    FRAME_ID: int = 0x2C # 帧ID
    FRAME_LENGTH: int = 47 # 帧长度
    MAX_BUFFER_LENGTH: int = 470 # 最大缓存长度

    buffer: bytearray = bytearray()
    lastValidFrame: bytes | None = None # 上一帧有效数据

    @classmethod
    def sensorInit(cls) -> None:
        '''初始化激光传感器'''
        cls.UART1.init(921600, 8, None, 1)
        cls.UART1.irq(cls.__uartCallback, UART.IRQ_RXIDLE)

    @classmethod
    def getClosestDistance(cls, data: bytes) -> float:
        '''获取最近的测量距离'''
        minDistance: float = float('inf')

        for index in range(6, len(data) - 5, 3):
            low = data[index]
            high = data[index + 1]
            distance: float = (high << 8) | low

            if (distance <= 0): continue

            minDistance = min(minDistance, distance)

        return minDistance
    
    @classmethod
    def processBuffer(cls) -> None:
        '''在主循环中调用, 用于从软件buffer中解析数据帧。'''
        while (len(cls.buffer) >= cls.FRAME_LENGTH):
            headerIndex = cls.buffer.find(cls.FRAME_HEADER)

            if (headerIndex == -1):
                cls.buffer = bytearray()
                return

            if (headerIndex > 0):
                cls.buffer = cls.buffer[headerIndex:]
                continue

            if (cls.buffer[1] == cls.FRAME_ID):
                frame = cls.buffer[:cls.FRAME_LENGTH]
                cls.lastValidFrame = bytes(frame)
                cls.buffer = cls.buffer[cls.FRAME_LENGTH:]
            else:
                cls.buffer = cls.buffer[1:]

    @classmethod
    def __uartCallback(cls, instance) -> None:
        '''UART中断回调函数, 读取数据存入buffer'''
        newData = instance.read()

        if (newData):
            cls.buffer.extend(newData)

        if (len(cls.buffer) > (cls.MAX_BUFFER_LENGTH)):
            cls.buffer = cls.buffer[-cls.FRAME_LENGTH:]
