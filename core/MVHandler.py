import sensor # type: ignore

from core.SensorHandler import SensorHandler

class MVHandler:
    CIRCLE_COLORS: list[tuple[int, int, int]] = [
        (128, 128, 128), # 索引0: 灰色 (占位符)
        (255,   0, 255), # 索引1: 品红 (对比绿色)
        (  0, 255, 255), # 索引2: 青色 (对比红色)
        (  0,   0, 255), # 索引3: 蓝色 (对比黄色)
    ]
    DETECTION_MAP: dict[int, str] = {
        1: 'GREEN',
        2: 'RED',
        3: 'YELLOW'
    }
    COLOR_THRESHOLDS: dict[int, tuple[int, int, int, int, int, int]] = {
        1: (0, 100, -128, -19, -128, 127), # 绿色
        2: (13, 45, 20, 57, -3, 22), # 红色
        3: (17, 100, -128, 127, 21, 127) # 黄色
    }

    MIN_CONFIDENCE: float = 0.4 # 目标识别的最小置信度
    MIN_TARGET_SIZE: int = 100 # 目标识别的最小像素面积

    LIGHT_MIN: int = 28 # 光线最小值, 低于此值则认为光线不足
    LIGHT_MAX: int = 30 # 光线最大值, 高于此值则认为光线过强
    GAIN: int = 10 # 曝光调整系数
    EXPOSURE_MIN: int = 50 # 最小曝光时间, 单位微秒
    EXPOSURE_MAX: int = 50000 # 最大曝光时间, 单位微秒

    currentTarget: int = 1 # 当前识别目标状态, 1: GREEN, 2: RED, 3: YELLOW
    isTargetTouched: bool = False # 当前目标是否已被“触碰”

    maxBlob: list[int] = [0, 0, 0, 0, 0, 0, 0, 0] # [x, y, w, h, pixels, cx, cy, rotation]
    maxSize: int = 0 # 当前识别像素的最大面积

    currentBrightness: int | float = 0 # 当前亮度
    currentExposure: int = 1000 # 当前曝光时间, 单位微秒(初始设置为1000)

    # 初始化摄像头
    @classmethod
    def mvInit(cls):
        '''初始化摄像头'''
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        sensor.skip_frames(30) # 等待摄像头稳定跳过的帧数
        sensor.set_auto_whitebal(False) # 关闭自动白平衡
        sensor.set_auto_gain(False) # 关闭自动增益
        sensor.set_auto_exposure(False, exposure_us=cls.currentExposure) # 关闭自动曝光, 设置曝光时间
    
    # 渲染当前需要识别的目标颜色
    @classmethod
    def renderCurrentTarget(cls, image):
        '''渲染当前需要识别的目标颜色'''
        image.draw_string(10, 10, 'NEEDED COLOR: ' + cls.DETECTION_MAP[cls.currentTarget])

    # 渲染当前屏幕亮度
    @classmethod
    def renderCurrentBrightness(cls, image):
        '''渲染当前屏幕亮度'''
        image.draw_string(10, 28, 'CURRENT BRIGHTNESS: ' + str(cls.currentBrightness))

    # 自动调整曝光时间
    @classmethod
    def autoAdjustExposure(cls, image):
        '''自动调整曝光时间'''
        stats = image.get_statistics()
        cls.currentBrightness = stats.l_mean() # 获取亮度

        if (cls.LIGHT_MIN < cls.currentBrightness < cls.LIGHT_MAX): return None

        # 计算曝光调整值
        targetBrightness = (cls.LIGHT_MIN + cls.LIGHT_MAX) / 2
        error = cls.currentBrightness - targetBrightness
        adjustment = cls.GAIN * error

        # 计算新的曝光时间, 并限制在合理范围内
        newExposure = cls.currentExposure - adjustment
        cls.currentExposure = int(max(min(newExposure, cls.EXPOSURE_MAX), cls.EXPOSURE_MIN))

        # 应用新的曝光时间
        sensor.set_auto_exposure(False, exposure_us=cls.currentExposure)
        
    # 重置最大目标信息
    @classmethod
    def resetMaxBlob(cls):
        '''重置最大目标信息'''
        cls.maxBlob = [0, 0, 0, 0, 0, 0, 0, 0]
        cls.maxSize = 0

    # 分析处理神经网络的输出结果, 返回(scores, maxConfidence, gridX, gridY)
    @classmethod
    def analyseResult(cls, result: list):
        '''分析处理神经网络的输出结果, 返回(scores, maxConfidence, gridX, gridY)'''
        scores = result[0][0] if (len(result[0].shape) == 4) else result[0]
        maxConfidence = 0
        bestX = 0
        bestY = 0
            
        for (yIndex, yValue) in enumerate(scores):
            for (xIndex, xValue) in enumerate(yValue):
                if (xValue[cls.currentTarget] <= maxConfidence): continue

                maxConfidence = max(xValue[cls.currentTarget], maxConfidence)
                bestX = xIndex
                bestY = yIndex

        return (scores, maxConfidence, bestX, bestY)

    # 获取最大目标的相关信息
    @classmethod
    def getMaxBlob(cls, image, scores, gridX: int, gridY: int):
        '''获取最大目标的相关信息'''
        gridH = scores.shape[-3]
        gridW = scores.shape[-2]

        roiW = int(image.width() / gridW)
        roiH = int(image.height() / gridH)
        roiX = int(gridX * roiW)
        roiY = int(gridY * roiH)

        expandedRoi = (
            max(0, roiX - 10),
            max(0, roiY - 10),
            min(image.width(), roiW + 20),
            min(image.height(), roiH + 20)
        )

        threshold = cls.COLOR_THRESHOLDS.get(cls.currentTarget, None)

        if (not threshold):
            return (0, 0, 0, 0, 0, 0, 0, 0)

        blobs = image.find_blobs([threshold], roi=expandedRoi, pixels_threshold=20, area_threshold=20, merge=True)

        if (not blobs):
            return (0, 0, 0, 0, 0, 0, 0, 0)
        
        maxBlob = blobs[0]
        x = maxBlob.x()
        y = maxBlob.y()
        w = maxBlob.w()
        h = maxBlob.h()
        pixels = maxBlob.pixels()
        centerX = maxBlob.cx()
        centerY = maxBlob.cy()
        rotation = maxBlob.rotation_deg()

        return (x, y, w, h, pixels, centerX, centerY, rotation)

    # 更新识别目标
    @classmethod
    def updateTargetState(cls, closestDistance: float, maxConfidence: float):
        '''更新识别目标'''
        isVisionLocked = cls.maxSize > cls.MIN_TARGET_SIZE and maxConfidence >= cls.MIN_CONFIDENCE
        isDistanceClose = closestDistance < SensorHandler.TOUCH_VALID_DISTANCE

        if (not isVisionLocked):
            cls.isTargetTouched = False
            return 'SEARCHING'
        
        if (isDistanceClose and not cls.isTargetTouched):
            cls.isTargetTouched = True
            cls.currentTarget += 1

            if (cls.currentTarget > 3):
                cls.currentTarget = 1

            return 'SWITCHED'
        
        if (not isDistanceClose):
            cls.isTargetTouched = False

        return 'TRACKING'
        
