from pyb import UART # type: ignore

class SensorHandler:
    lastValidFrame: bytes | None = None # 上一帧有效数据
    
    __UART1 = UART(1, 921600) # P0(RX), P1(TX)
    __FRAME_LENGTH: int = 47 # 帧长度
    __MIN_VALID_DISTANCE: int = 160 # 最小有效距离(mm)

    __buffer: bytearray = bytearray()

    @classmethod
    def sensorInit(cls) -> None:
        '''初始化激光传感器'''
        cls.__UART1.init(921600, 8, None, 1)
        cls.__UART1.irq(cls.__uartCallback, UART.IRQ_RXIDLE)

    @classmethod
    def getClosestDistance(cls, data: bytes) -> float:
        '''获取最近的测量距离'''
        minDistance: float | int = float('inf')

        for index in range(6, len(data) - 5, 3):
            low = data[index]
            high = data[index + 1]
            distance: float = (high << 8) | low
            
            if (distance <= cls.__MIN_VALID_DISTANCE): continue

            minDistance = min(minDistance, distance)

        if (minDistance == float('inf')): return float('inf')
                        
        return minDistance
    
    @classmethod
    def processBuffer(cls) -> None:
        '''在主循环中调用, 用于从软件buffer中解析数据帧。'''
        FRAME_HEADER: bytes = b'\x54' # 帧头    
        FRAME_ID: int = 0x2C # 帧ID

        while (len(cls.__buffer) >= cls.__FRAME_LENGTH):
            headerIndex = cls.__buffer.find(FRAME_HEADER)

            if (headerIndex == -1):
                cls.__buffer = bytearray()
                return

            if (headerIndex > 0):
                cls.__buffer = cls.__buffer[headerIndex:]
                continue

            if (cls.__buffer[1] == FRAME_ID):
                frame = cls.__buffer[:cls.__FRAME_LENGTH]
                cls.lastValidFrame = bytes(frame)
                cls.__buffer = cls.__buffer[cls.__FRAME_LENGTH:]
            else:
                cls.__buffer = cls.__buffer[1:]

    @classmethod
    def __uartCallback(cls, instance) -> None:
        '''UART中断回调函数, 读取数据存入buffer'''
        MAX_BUFFER_LENGTH: int = 470 # 最大缓存长度

        newData = instance.read()

        if (newData):
            cls.__buffer.extend(newData)

        if (len(cls.__buffer) > (MAX_BUFFER_LENGTH)):
            cls.__buffer = cls.__buffer[-cls.__FRAME_LENGTH:]
