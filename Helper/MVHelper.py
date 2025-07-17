import sensor, pyb, time #type:ignore

from Helper.BlobHelper import BlobHelper
from Helper.DetectionHelper import DetectionHelper
from image import Image #type:ignore

class MVHelper:
    flagFind = 1 #当前识别目标状态, 1: RED, 2: YELLOW, 3: BLACK
    maxBlob = [0, 0, 0, 0, 0, 0, 0, 0] #[x, y, w, h, pixels, cx, cy, rotation]
    maxSize = 0 #当前识别像素的最大面积
    minConfidence = 0.8 if (flagFind == 3) else 0.97

    neededCheckTimes = 3 #默认识别次数. 黑色需要 4 次, 其他颜色需要 3 次
    lastDetectedType = None #上次识别的目标颜色
    stableFrames = 0 #当前稳定识别的帧数

    lightMin = 30 #光线最小值, 低于此值则认为光线不足
    lightMax = 45 #光线最大值, 高于此值则认为光线过强
    currentBrightness: int | float = 0 #当前亮度
    currentExposure = 1000 #当前曝光时间, 单位微秒(初始设置为1000)

    clock = time.clock() #type:ignore
    UART3 = pyb.UART(3, 115200)

    #初始化摄像头
    @classmethod
    def mvInit(cls):
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        sensor.skip_frames(30) #等待摄像头稳定跳过的帧数
        sensor.set_auto_whitebal(False) #关闭自动白平衡
        sensor.set_auto_gain(False) #关闭自动增益
        sensor.set_auto_exposure(False, exposure_us = cls.currentExposure) #关闭自动曝光, 设置曝光时间

        cls.clock = cls.clock.tick() 
        cls.UART3 = pyb.UART(3, 115200) #初始化 UART3

        cls.UART3.init(115200, 8, None, 1) 

    #判别当前目标识别是否稳定
    @classmethod
    def targetTypeStablize(cls, targetType: str):
        if targetType == cls.lastDetectedType:
            cls.stableFrames += 1
        else:
            cls.stableFrames = 0
            cls.lastDetectedType = targetType

    #状态转换, 切换识别颜色目标
    @classmethod
    def stateTransform(cls, img: Image, blob: list[int], targetType: str):
        cls.targetTypeStablize(targetType)

        DetectionHelper.detectCount += 1 if cls.stableFrames >= 12 else 0
        requiredCheckTimes = cls.neededCheckTimes + 1 if targetType == 'BLACK' else cls.neededCheckTimes

        if (DetectionHelper.detectCount >= requiredCheckTimes):
            cls.maxSize = 0
            cls.flagFind += 1
            DetectionHelper.detectCount = 0
            cls.stableFrames = 0

        if (cls.flagFind >= 4):
            cls.flagFind = 1

        if (BlobHelper.getW(blob) * BlobHelper.getH(blob) > cls.maxSize):
            cls.maxBlob = blob
            cls.maxSize = BlobHelper.getW(blob) * BlobHelper.getH(blob)
    
    #渲染当前需要识别的目标颜色
    @classmethod
    def renderCurrentTargetString(cls, image: Image):
        for keyIndex in range(0, 4):
            key = (keyIndex, cls.flagFind)

            if key in DetectionHelper.detectionMap:
                targetType = DetectionHelper.detectionMap[key]

                image.draw_string(10, 10, 'NEEDED COLOR: ' + targetType)

    #渲染当前识别次数
    @staticmethod
    def renderCurrentTargetCount(image: Image):
        image.draw_string(10, 28, 'CURRENT COUNT: ' + str(DetectionHelper.detectCount))

    #渲染当前屏幕亮度
    @classmethod
    def renderCurrentBrightness(cls, image: Image):
        image.draw_string(10, 46, 'CURRENT BRIGHTNESS: ' + str(cls.currentBrightness))

    #渲染当前识别的最大圆形目标
    @staticmethod
    def validateCircle(image: Image):
        circles = image.find_circles(threshold = 5000, 
            x_margin = 10, y_margin = 10, r_margin = 10,
            r_min = 30, r_max = 50, r_step = 2
        )
        
        if (circles):
            circle = max(circles, key = lambda c: c.r())
            area = (circle.x() - circle .r(), circle.y() - circle.r(), 2 * circle.r(), 2 * circle.r())
            
            image.draw_rectangle(area, color = (255, 0, 0))
            image.draw_string(10, 46, 'VALID CIRCLE')

    #自动调整曝光时间
    @classmethod
    def autoAdjustExposure(cls, image: Image):
        
        stats = image.get_statistics()
        cls.currentBrightness = stats.l_mean() #获取亮度

        if (cls.currentBrightness < cls.lightMin):
            sensor.set_auto_exposure(False, exposure_us = cls.currentExposure + 1000)

            cls.currentExposure += 1000
        elif (cls.currentBrightness > cls.lightMax):
            exposure = max(1000, cls.currentExposure - 1000)

            sensor.set_auto_exposure(False, exposure_us = exposure)
            
            cls.currentExposure = exposure
