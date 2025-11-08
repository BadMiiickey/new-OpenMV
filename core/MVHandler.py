import sensor # type: ignore

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

    MIN_TOUCH_SIZE_THRESHOLDS: dict[int, int] = {
        1: 500, # 绿色触碰识别的最小像素面积
        2: 900, # 红色触碰识别的最小像素面积
        3: 1000  # 黄色触碰识别的最小像素面积
    } # 触碰识别的最小像素面积
    MIN_RECOGNIZED_CONFIDENCES: dict[int, float] = {
        1: 0.5, # 绿色识别的最小置信度
        2: 0.5, # 红色识别的最小置信度
        3: 0.5  # 黄色识别的最小置信度
    }
    COLOR_THRESHOLDS: dict[int, tuple[int, int, int, int, int, int]] = {
        1: (24, 95, -58, -26, 3, 58),   # 绿色阈值
        2: (0, 82, 12, 64, 10, 91),   # 红色阈值
        3: (15, 100, -21, 29, 31, 105),   # 黄色阈值
    }
    TOUCH_VALID_DISTANCE: int = 200  # 有效触碰距离, 小于此值则认为是触碰
    MODIFY_DISTANCE: int = 200 # 认为船体触碰非目标物需要微调的距离

    LIGHT_MIN: int = 40 # 光线最小值, 低于此值则认为光线不足
    LIGHT_MAX: int = 42 # 光线最大值, 高于此值则认为光线过强
    GAIN: int = 10 # 曝光调整系数
    EXPOSURE_MIN: int = 10 # 最小曝光时间, 单位微秒
    EXPOSURE_MAX: int = 50000 # 最大曝光时间, 单位微秒

    imageWidth: int = 0 # 图像宽度
    imageHeight: int = 0 # 图像高度

    maxBlob: tuple[int, int, int, int, int, int, int, int] = (0, 0, 0, 0, 0, 0, 0, 0) # 当前识别的最大像素
    maxSize: int = 0 # 当前识别像素的最大面积

    currentTarget: int = 2 # 当前识别目标状态, 1: GREEN, 2: RED, 3: YELLOW
    currentColorThreshold: tuple[int, int, int, int, int, int] = (0, 0, 0, 0, 0, 0) # 当前颜色阈值
    currentBrightness: int = 0 # 当前亮度
    currentExposure: int = 1000 # 当前曝光时间, 单位微秒(初始设置为1000)
    currentAverageConfidence: float = 0.0 # 当前平均置信度

    lastAction: str = '' # 上一次执行的动作

    @classmethod
    def mvInit(cls) -> None:
        '''初始化摄像头'''
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        sensor.skip_frames(30) # 等待摄像头稳定跳过的帧数
        sensor.set_auto_whitebal(False) # 关闭自动白平衡
        sensor.set_auto_gain(False) # 关闭自动增益
        sensor.set_auto_exposure(False, exposure_us=cls.currentExposure) # 关闭自动曝光, 设置曝光时间

        cls.imageWidth = sensor.snapshot().width()
        cls.imageHeight = sensor.snapshot().height()
    
    @classmethod
    def renderCurrentTarget(cls, image) -> None:
        '''渲染当前需要识别的目标颜色'''
        image.draw_string(10, 10, 'NEEDED COLOR: ' + cls.DETECTION_MAP[cls.currentTarget])

    @classmethod
    def renderCurrentBrightness(cls, image) -> None:
        '''渲染当前屏幕亮度'''
        image.draw_string(10, 28, 'CURRENT BRIGHTNESS: ' + str(cls.currentBrightness))

    @classmethod
    def autoAdjustExposure(cls, image) -> None:
        '''自动调整曝光时间'''
        stats = image.get_statistics()
        cls.currentBrightness = stats.l_mean() # 获取亮度

        if (cls.LIGHT_MIN < cls.currentBrightness < cls.LIGHT_MAX): return None

        # 计算曝光调整值
        targetBrightness: float = (cls.LIGHT_MIN + cls.LIGHT_MAX) / 2
        error: float = cls.currentBrightness - targetBrightness
        adjustment: float = cls.GAIN * error

        # 计算新的曝光时间, 并限制在合理范围内
        newExposure: float = cls.currentExposure - adjustment
        cls.currentExposure = int(max(min(newExposure, cls.EXPOSURE_MAX), cls.EXPOSURE_MIN))

        # 应用新的曝光时间
        sensor.set_auto_exposure(False, exposure_us=cls.currentExposure)
        
    @classmethod
    def resetMaxBlob(cls) -> None:
        '''重置最大目标信息'''
        cls.maxBlob = (0, 0, 0, 0, 0, int(cls.imageWidth / 2), int(cls.imageHeight / 2), 0)
        cls.maxSize = 0

    @classmethod
    def analyseResult(cls, result: list) -> tuple[list[list[list[float]]], float, int, int]:
        '''分析处理神经网络的输出结果, 返回(scores, maxConfidence, gridX, gridY)'''
        scores: list[list[list[float]]] = result[0][0]
        confidenceThreshold: float = cls.MIN_RECOGNIZED_CONFIDENCES.get(cls.currentTarget, 1)
        totalConfidence: float = 0.0
        totalX: int | float = 0
        totalY: int | float = 0
        count: int = 0

        for (yIndex, yValue) in enumerate(scores):
            for (xIndex, xValue) in enumerate(yValue):
                if (xValue[cls.currentTarget] <= confidenceThreshold): continue

                totalConfidence += xValue[cls.currentTarget]
                totalX += xIndex / len(yValue) * cls.imageWidth
                totalY += yIndex / len(scores) * cls.imageHeight
                count += 1

        averageConfidence: float = totalConfidence / count if (count > 0) else 0.0
        averageX: int = int(round(totalX / count)) if (count > 0) else 0
        averageY: int = int(round(totalY / count)) if (count > 0) else 0

        return (scores, averageConfidence, averageX, averageY)

    @classmethod
    def getMaxBlob(cls, image, scores, gridX: int, gridY: int, distance: float) -> tuple[int, int, int, int, int, int, int, int]:
        '''获取最大目标的相关信息'''
        if (distance >= cls.TOUCH_VALID_DISTANCE):
            gridH: int = scores.shape[-3]
            gridW: int = scores.shape[-2]

            roiW: int = int(cls.imageWidth / gridW)
            roiH: int = int(cls.imageHeight / gridH)
            roiX: int = gridX - roiW // 2
            roiY: int = gridY - roiH // 2

            searchRoi: tuple[int, int, int, int] = (
                max(0, roiX - 10),
                max(0, roiY - 10),
                min(image.width(), roiW + 20),
                min(image.height(), roiH + 20)
            )
        else:
            searchRoi = (0, 0, cls.imageWidth, cls.imageHeight)

        threshold: tuple[int, int, int, int, int, int] | None = cls.COLOR_THRESHOLDS.get(cls.currentTarget, None)

        if (not threshold): return cls.maxBlob

        blobs = image.find_blobs([threshold], roi=searchRoi, pixels_threshold=20, area_threshold=20, merge=True)

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
        isTouched: bool = closestDistance < cls.TOUCH_VALID_DISTANCE \
            and cls.maxSize > cls.MIN_TOUCH_SIZE_THRESHOLDS.get(cls.currentTarget, 0)
        isDistanceCloseNotTarget: bool = closestDistance < cls.MODIFY_DISTANCE \
            and cls.maxSize <= cls.MIN_TOUCH_SIZE_THRESHOLDS.get(cls.currentTarget, 0)
        isRecognized: bool = maxConfidence > cls.MIN_RECOGNIZED_CONFIDENCES.get(cls.currentTarget, 1)

        if (isTouched):
            cls.currentTarget = cls.currentTarget % 3 + 1

            return 'SWITCHED'
        elif (isRecognized): return 'TRACKING'
        elif (isDistanceCloseNotTarget): return 'MODIFYING'
        else: return 'SEARCHING'

