import Helper.DetectionHelper as DetectionHelper
import sensor, time #type:ignore

from Helper.DetectionHelper import DetectionHelper
from image import Image #type:ignore

class MVHelper:
    flagFind = 1
    maxBlob = [0, 0, 0, 0, 0, 0, 0, 0] #[x, y, w, h, pixels, cx, cy, rotation]
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
        sensor.set_auto_whitebal(False)
        sensor.set_auto_gain(False)

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

        if (cls.flagFind >= 4):
            cls.flagFind = 1

        if (myBlob.w() * myBlob.h() > cls.maxSize): #type:ignore
            cls.maxBlob = myBlob
            cls.maxSize = myBlob[2] * myBlob[3]

        return myCount
    
    @staticmethod
    def renderCurrentTargetString():
        for keyIndex in range(0, 4):
            key = (keyIndex, MVHelper.flagFind)

            if key in DetectionHelper.detectionMap:
                targetType = DetectionHelper.detectionMap[key]

                img.draw_string(10, 10, targetType + '!') #type:ignore