import sensor, time

from image import Image

class MVHelper:
    flagFind = 1
    maxBlob = [0, 0, 0, 0]  # 应该是 [x, y, width, height]
    maxSize = 0
    neededCheckTimes = 3

    #默认室外环境配置
    def __init__(self, autoWhiteBal = False, autoGain = False, autoExposure = False, exposureUs = 2500):
        self.mvInit()
        self.setMVParams(autoWhiteBal, autoGain, autoExposure, exposureUs)

    #初始化摄像头
    @staticmethod
    def mvInit():
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        sensor.skip_frames(10)

    #自动检测环境并初始化摄像头
    @staticmethod
    def autoDetectEnvironment():
        MVHelper.mvInit()

        #默认室外环境
        sensor.set_auto_whitebal(False)
        sensor.set_auto_gain(False)
        sensor.set_auto_exposure(False, exposure_us = 2500)

        totalBrightness = 0
        samples = 5

        for sample in range(samples):
            img = sensor.snapshot()
            totalBrightness += img.get_statistics().mean()
            time.sleep_ms(100)
        
        averageBrightness = totalBrightness / samples

        return MVHelper(False, False, False, 2500) if averageBrightness > 120 else MVHelper(True, True, True, 4000)

    #设置摄像头曝光状态
    @staticmethod
    def setMVParams(autoWhiteBal: bool, autoGain: bool, autoExposure: bool, exposureUs: int):
        sensor.set_auto_whitebal(autoWhiteBal)
        sensor.set_auto_gain(autoGain)
        sensor.set_auto_exposure(autoExposure, exposure_us = exposureUs)

    #状态转换, 切换识别颜色目标
    @classmethod
    def stateTransform(cls, img: Image, myBlob: list[int], myCount: int, targetType: str):
        requiredCheckTimes = cls.neededCheckTimes + 1 if targetType == 'BLACK' else cls.neededCheckTimes
        myCount += 1

        if (myCount >= requiredCheckTimes):
            cls.maxSize = 0
            cls.flagFind += 1

            if cls.flagFind >= 4:
                cls.flagFind = 1
            
            myCount = 0

        blobSize = myBlob[2] * myBlob[3]

        if (blobSize > cls.maxSize):
            cls.maxBlob = myBlob
            cls.maxSize = blobSize

        return myCount