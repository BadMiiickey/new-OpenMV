import sensor, pyb, time # type: ignore

from core.DetectionHandler import DetectionHandler

from image import Image # type: ignore

class MVHandler:
    currentTarget: int = 2 # 当前识别目标状态, 1: GREEN, 2: RED, 3: YELLOW
    maxBlob: list[int] = [0, 0, 0, 0, 0, 0, 0, 0] # [x, y, w, h, pixels, cx, cy, rotation]
    maxSize: int = 0 # 当前识别像素的最大面积
    minConfidence: float = 0.8

    lastDetectedType: str | None = None # 上次识别的目标颜色

    lightMin: int = 30 # 光线最小值, 低于此值则认为光线不足
    lightMax: int = 45 # 光线最大值, 高于此值则认为光线过强
    currentBrightness: int | float = 0 # 当前亮度
    currentExposure: int = 30000 # 当前曝光时间, 单位微秒(初始设置为30000)

    clock = time.clock() # type: ignore
    UART3 = pyb.UART(3, 115200) # P4(TX), P5(RX)

    # 初始化摄像头
    @classmethod
    def mvInit(cls):
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        sensor.skip_frames(30) # 等待摄像头稳定跳过的帧数
        sensor.set_auto_whitebal(False) # 关闭自动白平衡
        sensor.set_auto_gain(False) # 关闭自动增益
        sensor.set_auto_exposure(False, exposure_us = cls.currentExposure) # 关闭自动曝光, 设置曝光时间

        cls.clock = cls.clock.tick() 

        cls.UART3.init(115200, 8, None, 1)
    
    # 渲染当前需要识别的目标颜色
    @classmethod
    def renderCurrentTargetString(cls, image: Image):
        image.draw_string(10, 10, 'NEEDED COLOR: ' + DetectionHandler.detectionMap[cls.currentTarget])

    # 渲染当前识别次数
    @staticmethod
    def renderCurrentTargetCount(image: Image):
        image.draw_string(10, 28, 'CURRENT COUNT: ' + str(DetectionHandler.detectCount))

    # 渲染当前屏幕亮度
    @classmethod
    def renderCurrentBrightness(cls, image: Image):
        image.draw_string(10, 46, 'CURRENT BRIGHTNESS: ' + str(cls.currentBrightness))

    # 自动调整曝光时间
    @classmethod
    def autoAdjustExposure(cls, image: Image):
        stats = image.get_statistics()
        cls.currentBrightness = stats.l_mean() #获取亮度

        if (cls.currentBrightness < cls.lightMin):
            sensor.set_auto_exposure(False, exposure_us = cls.currentExposure + 1000)

            cls.currentExposure += 1000
            
            return None
        
        exposure = max(1000, cls.currentExposure - 1000)
        cls.currentExposure = exposure

        sensor.set_auto_exposure(False, exposure_us = exposure)
