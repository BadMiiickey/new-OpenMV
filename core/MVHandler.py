import sensor # type: ignore

class MVHandler:
    TOUCH_VALID_DISTANCE: int = 200  # 有效触碰距离, 小于此值则认为是触碰
    NN_FAILURE_TOLERANCE: int = 3 # 连续失败3次后，才真正认为目标丢失

    maxBlob: tuple[int, int, int, int, int, int, int, int] = (0, 0, 0, 0, 0, 0, 0, 0) # 当前识别的最大像素
    maxSize: int = 0 # 当前识别像素的最大面积
    currentTarget: int = 2 # 当前识别目标状态, 1: GREEN, 2: RED, 3: YELLOW
    currentAverageConfidence: float = 0.0 # 当前平均置信度

    __MIN_RECOGNIZED_CONFIDENCES: dict[int, float] = {
        1: 0.6, # 绿色识别的最小置信度
        2: 0.6, # 红色识别的最小置信度
        3: 0.9  # 黄色识别的最小置信度
    }
    __COLOR_THRESHOLDS: dict[int, tuple[int, int, int, int, int, int]] = {
        1: (0, 100, -41, -14, -39, 32),   # 绿色阈值
        2: (0, 100, 21, 67, -24, 34),   # 红色阈值
        3: (0, 100, -11, 25, 13, 63),   # 黄色阈值
    }
    
    __imageWidth: int = 0 # 图像宽度
    __imageHeight: int = 0 # 图像高度
    __currentBrightness: int = 0 # 当前亮度
    __currentExposure: int = 1000 # 当前曝光时间, 单位微秒(初始设置为1000)

    @classmethod
    def mvInit(cls) -> None:
        '''初始化摄像头'''
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        sensor.skip_frames(30) # 等待摄像头稳定跳过的帧数
        sensor.set_auto_whitebal(False) # 关闭自动白平衡
        sensor.set_auto_gain(False) # 关闭自动增益
        sensor.set_auto_exposure(False, exposure_us=cls.__currentExposure) # 关闭自动曝光, 设置曝光时间

        firstImage = sensor.snapshot()
        cls.__imageWidth = firstImage.width()
        cls.__imageHeight = firstImage.height()

    @classmethod
    def autoAdjustExposure(cls, image, roi: tuple[int, int, int, int]) -> None:
        '''自动调整曝光时间'''
        LIGHT_MIN: int = 40 # 光线最小值, 低于此值则认为光线不足
        LIGHT_MAX: int = 42 # 光线最大值, 高于此值则认为光线过强
        GAIN: int = 10 # 曝光调整系数
        EXPOSURE_MIN: int = 10 # 最小曝光时间, 单位微秒
        EXPOSURE_MAX: int = 50000 # 最大曝光时间, 单位微秒
        DEFAULT_ROI_SIZE: int = 80 # 计算亮度的ROI区域大小

        if (not roi or roi[2] <= 0 or roi[3] <= 0):
            roiX: int = (cls.__imageWidth - DEFAULT_ROI_SIZE) // 2
            roiY: int = (cls.__imageHeight - DEFAULT_ROI_SIZE) // 2
            centerRoi: tuple[int, int, int, int] = (roiX, roiY, DEFAULT_ROI_SIZE, DEFAULT_ROI_SIZE)
        else:
            centerRoi = roi

        stats = image.get_statistics(roi=centerRoi)
        cls.__currentBrightness = stats.l_mean() # 获取亮度

        if (LIGHT_MIN < cls.__currentBrightness < LIGHT_MAX): return None

        # 计算曝光调整值
        targetBrightness: float = (LIGHT_MIN + LIGHT_MAX) / 2
        error: float = cls.__currentBrightness - targetBrightness
        adjustment: float = GAIN * error

        # 计算新的曝光时间, 并限制在合理范围内
        newExposure: float = cls.__currentExposure - adjustment
        cls.__currentExposure = int(max(min(newExposure, EXPOSURE_MAX), EXPOSURE_MIN))

        # 应用新的曝光时间
        sensor.set_auto_exposure(False, exposure_us=cls.__currentExposure)

    @classmethod
    def resetMaxBlob(cls) -> None:
        '''重置最大目标信息'''
        cls.maxBlob = (0, 0, 0, 0, 0, int(cls.__imageWidth / 2), int(cls.__imageHeight / 2), 0)
        cls.maxSize = 0

    @classmethod
    def analyseResult(cls, result: list) -> tuple[float, int]:
        '''分析处理神经网络的输出结果, 返回峰值置信度与加权平均x坐标'''
        scores: list[list[list[float]]] = result[0][0]
        confidenceThreshold: float = cls.__MIN_RECOGNIZED_CONFIDENCES.get(cls.currentTarget, 1)

        totalConfidenceWeight: float = 0.0
        weightedX: int | float = 0
        peakConfidence: float = 0.0

        for (_, yValue) in enumerate(scores):
            for (xIndex, xValue) in enumerate(yValue):
                confidence: float = xValue[cls.currentTarget]

                if (confidence <= confidenceThreshold): continue

                peakConfidence = confidence if (confidence > peakConfidence) else peakConfidence
                totalConfidenceWeight += confidence
                weightedX += xIndex / len(yValue) * cls.__imageWidth * confidence

        averageX: int = int(round(weightedX / totalConfidenceWeight)) if (totalConfidenceWeight > 0) else 0

        return (peakConfidence, averageX)

    @classmethod
    def getMaxBlob(cls, image) -> tuple[int, int, int, int, int, int, int, int]:
        '''获取最大目标的相关信息'''
        threshold: tuple[int, int, int, int, int, int] | None = cls.__COLOR_THRESHOLDS.get(cls.currentTarget, None)

        if (threshold is None): return cls.maxBlob

        blobs = image.find_blobs([threshold], pixels_threshold=1000, area_threshold=1000, merge=True)

        if (not blobs): return cls.maxBlob
        
        maxBlob = blobs[0]
        x: int = maxBlob.x()
        y: int = maxBlob.y()
        w: int = maxBlob.w()
        h: int = maxBlob.h()
        pixels: int = maxBlob.pixels()
        centerX: int = maxBlob.cx()
        centerY: int = maxBlob.cy()
        rotation: int = maxBlob.rotation()

        return (x, y, w, h, pixels, centerX, centerY, rotation)

    @classmethod
    def updateTargetState(cls, closestDistance: float, maxConfidence: float) -> str:
        '''更新识别目标'''
        MODIFY_DISTANCE: int = 200 # 认为船体触碰非目标物需要微调的距离
        MIN_TOUCH_SIZE_THRESHOLDS: dict[int, int] = {
            1: 18000, # 绿色触碰识别的最小像素面积
            2: 13000, # 红色触碰识别的最小像素面积
            3: 20000  # 黄色触碰识别的最小像素面积
        } # 触碰识别的最小像素面积

        isTouched: bool = closestDistance < cls.TOUCH_VALID_DISTANCE \
            and cls.maxSize > MIN_TOUCH_SIZE_THRESHOLDS.get(cls.currentTarget, 999999)
        isRecognized: bool = maxConfidence > cls.__MIN_RECOGNIZED_CONFIDENCES.get(cls.currentTarget, 1)
        isDistanceCloseNotTarget: bool = closestDistance < MODIFY_DISTANCE and not isTouched

        if (isTouched):
            cls.currentTarget = cls.currentTarget % 3 + 1

            return 'SWITCHED'
        elif (isRecognized): return 'TRACKING'
        elif (isDistanceCloseNotTarget): return 'MODIFYING'
        else: return 'SEARCHING'

