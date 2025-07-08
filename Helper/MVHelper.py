import sensor, pyb, time #type:ignore

from Helper.BlobHelper import BlobHelper
from Helper.DetectionHelper import DetectionHelper
from image import Image #type:ignore

class MVHelper:
    flagFind = 1
    maxBlob = [0, 0, 0, 0, 0, 0, 0, 0] #[x, y, w, h, pixels, cx, cy, rotation]
    maxSize = 0
    neededCheckTimes = 3
    lastDetectedType = None
    stableFrames = 0
    clock = time.clock() #type:ignore
    UART3 = pyb.UART(3, 115200)

    #初始化摄像头
    @classmethod
    def mvInit(cls):
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        sensor.skip_frames(10)
        sensor.set_auto_whitebal(False)
        sensor.set_auto_gain(False)

        cls.clock = cls.clock.tick()
        cls.UART3 = pyb.UART(3, 115200)

        cls.UART3.init(115200, 8, None, 1)

    #设置摄像头曝光状态
    @staticmethod
    def setMVParams(autoWhiteBal: bool, autoGain: bool, autoExposure: bool, exposureUs: int):
        sensor.set_auto_whitebal(autoWhiteBal)
        sensor.set_auto_gain(autoGain)
        sensor.set_auto_exposure(autoExposure, exposure_us = exposureUs)

    #状态转换, 切换识别颜色目标
    @classmethod
    def stateTransform(cls, img: Image, blob: list[int], targetType: str):
        if targetType == cls.lastDetectedType:
            cls.stableFrames += 1
        else:
            cls.stableFrames = 0
            cls.lastDetectedType = targetType
        
        minStableFrames = 12

        if cls.stableFrames >= minStableFrames:
            DetectionHelper.detectCount += 1

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
    def renderCurrentTargetCount(image: Image, detectCount: int):
        image.draw_string(10, 28, 'CURRENT COUNT: ' + str(detectCount))

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