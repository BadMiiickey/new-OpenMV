from pyb import UART # type: ignore

class SensorHandler:
    UART1 = UART(1, 921600)  # P0(RX), P1(TX)
    MIN_VALID_DISTANCE: int = 110  # 最小有效距离, 小于此值则认为测量无效
    TOUCH_VALID_DISTANCE: int = 360  # 有效触碰距离, 小于此值则认为是触碰

    FRAME_HEADER: bytes = b'\x54'  # 帧头
    FRAME_LENGTH: int = 47  # 帧长度
    MAX_BUFFER_LENGTH: int = 470  # 最大缓存长度

    buffer: bytearray = bytearray()  # 用于存储接收到的数据

    @classmethod
    def sensorInit(cls):
        '''初始化激光传感器'''
        cls.UART1.init(921600, 8, None, 1)

    @classmethod
    def readFrame(cls):
        '''读取一帧数据, 返回完整的47字节数据, 帧头为0x54'''
        data = cls.UART1.any()
        
        if (data):
            cls.buffer.extend(cls.UART1.read(data))
        
        headerIndex = cls.buffer.find(cls.FRAME_HEADER)

        if (headerIndex == -1):
            if (len(cls.buffer) >= cls.FRAME_LENGTH):
                cls.buffer = cls.buffer[-cls.FRAME_LENGTH:]  # 保留最后46字节，防止丢失帧头

            return None
            
        if (headerIndex > 0):
            cls.buffer = cls.buffer[headerIndex:]  # 丢弃帧头前的数据

        if (len(cls.buffer) >= cls.FRAME_LENGTH):
            frame = cls.buffer[:cls.FRAME_LENGTH]
            cls.buffer = cls.buffer[cls.FRAME_LENGTH:]  # 移除已处理的数据
            return frame
        
        return None

    @classmethod
    def getClosestDistance(cls, data):
        '''获取最近的测量距离'''
        minDistance = float('inf')

        for i in range(6, len(data) - 2, 3):
            distance = data[i] + (data[i + 1] << 8)
            minDistance = min(minDistance, distance) if (distance >= cls.MIN_VALID_DISTANCE) else minDistance

        return minDistance