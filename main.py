import sensor, time, tf, uos, gc, math #type:ignore

from Helper.LEDHelper import LEDHelper
from Helper.BlobHelper import BlobHelper
from Helper.ColorsHelper import ColorsHelper
from Helper.DetectionHelper import DetectionHelper
from Helper.MVHelper import MVHelper
from Helper.PIDHelper import PIDHelper
from Helper.TimeHelper import TimeHelper
from Helper.MotorHelper import MotorHelper
from Helper.PrintHelper import PrintHelper

#机器学习文件加载
try:
    net = tf.load("trained.tflite", load_to_fb = uos.stat('trained.tflite')[6] > (gc.mem_free() - (64 * 1024))) #type:ignore
except Exception as e:
    raise Exception('Failed to load "trained.tflite" (' + str(e) + ')')
try:
    labels = [line.rstrip('\n') for line in open("labels.txt")]
except Exception as e:
    raise Exception('Failed to load "labels.txt" (' + str(e) + ')')

#涡轮初始化
MotorHelper.motorInit()
MotorHelper.setMotorSpeed(7.5, 7.5)
time.sleep(6) #极度玄学, 慎调!

#OpenMV初始化
MVHelper.mvInit()

#PID初始实例化
xPid = PIDHelper(1, 1, 0, 100)
hPid = PIDHelper(0.01, 0.01, 0, 100)

#循环执行部分
while(True):
    MVHelper.clock
    MVHelper.maxSize = 0
    image = sensor.snapshot()

    #终端输出
    PrintHelper.messagePrint(3)

    #自动曝光调整
    MVHelper.autoAdjustExposure(image)

    #LED
    # LEDHelper.toggleLED(2, 0.5) #OpenMV绿色LED闪烁
    LEDHelper.showCurrentTarget(MVHelper.flagFind) #编号[1] = 红色, [2] = 绿色, [3] = 蓝色

    #渲染当前目标信息
    MVHelper.renderCurrentTargetString(image)
    MVHelper.renderCurrentTargetCount(image)
    MVHelper.renderCurrentBrightness(image)

    #渲染当前识别出的最大圆
    MVHelper.validateCircle(image)

    #检测目标是否存在
    for keyIndex, valueList in enumerate(net.detect(image, thresholds = [(math.ceil(MVHelper.minConfidence * 255), 255)])):
        if (keyIndex == 0): continue
        if (len(valueList) == 0): 
            key = (keyIndex, MVHelper.flagFind)

            if (key in DetectionHelper.detectionMap):
                MVHelper.maxSize = 0
            
            continue

        #渲染圆标记目标位置
        for value in valueList:
            blob = value.rect()
            centerX = math.floor(BlobHelper.getX(blob) + BlobHelper.getW(blob) / 2)
            centerY = math.floor(BlobHelper.getY(blob) + BlobHelper.getH(blob) / 2)
            key = (keyIndex, MVHelper.flagFind)

            image.draw_circle((centerX, centerY, 12), color = ColorsHelper.circleColors[keyIndex], thickness = 2)

            if (key in DetectionHelper.detectionMap):
                targetType = DetectionHelper.detectionMap[key]
                
                MVHelper.stateTransform(image, blob, targetType)

    #读取串口
    if (MVHelper.UART3.any()):
        data = MVHelper.UART3.read()

        if (len(data) == 0): continue
        if (
            data[0] == 0xA5
            and data[3] == 0x5A
            and data[1] != 0
            and data[2] != 0
        ):
            MotorHelper.isAutoControl = False

    #手动控制逻辑
    if (not MotorHelper.isAutoControl):
        MotorHelper.leftCtrl = MotorHelper.linearMap(data[1], 110, 200, 5, 10) if (data[1] != 0 and data[2] != 0) else 7.5
        MotorHelper.rightCtrl = MotorHelper.linearMap(data[2], 110, 200, 5, 10) if (data[1] != 0 and data[2] != 0) else 7.5

        MotorHelper.setMotorSpeed(MotorHelper.leftCtrl, MotorHelper.rightCtrl)
        TimeHelper.updateLastTimeWhenNotAutoControl()
        continue

    #未检测到目标
    if (MVHelper.maxSize == 0):
        MotorHelper.setMotorSpeed(7.7, 7.0) #设置电机转速, 使得小船原地旋转
        continue

    #忽略过小目标
    if (BlobHelper.getW(MVHelper.maxBlob) * BlobHelper.getH(MVHelper.maxBlob) <= 100): continue

    #自动控制逻辑
    #计算水平(xError)误差
    xError = math.floor(BlobHelper.getX(MVHelper.maxBlob) + BlobHelper.getW(MVHelper.maxBlob) / 2 - image.width() / 2)
    hError = BlobHelper.getW(MVHelper.maxBlob) * BlobHelper.getH(MVHelper.maxBlob) - ColorsHelper.sizeThreshold

    #计算水平(xOutput)及距离控制量绝对值(hOutput)
    xOutput = xPid.getPid(xError, 1)
    hOutput = hPid.getPid(hError, 1)

    #差动驱动控制
    MotorHelper.leftOut = min(500, -xOutput - hOutput)
    MotorHelper.rightOut = min(500, xOutput - hOutput)

    #计算映射后的实际电机速度
    MotorHelper.mappedA = MotorHelper.linearMap(MotorHelper.leftOut, 0, 500, 7.7, 8.5)
    MotorHelper.mappedB = MotorHelper.linearMap(MotorHelper.rightOut, 0, 500, 7.7, 8.5)

    image.draw_rectangle(MVHelper.maxBlob[0 : 4], color = (255, 0, 0))
    MotorHelper.setMotorSpeed(MotorHelper.mappedA, MotorHelper.mappedB)
    TimeHelper.updateLastTime()