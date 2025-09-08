import sensor, ml, uos, gc, math # type: ignore

from core.BlobHandler import BlobHandler
from core.ColorsHandler import ColorsHandler
from core.DetectionHandler import DetectionHandler
from core.LEDHandler import LEDHandler
from core.MVHandler import MVHandler
from core.MotorHandler import MotorHandler
from core.SensorHandler import SensorHandler

from pid import PID # type: ignore

# *** <- 大部分封装类仅被调用一次, 因此无需实例化, 直接作为工具类使用即可 -> *** #

# 机器学习文件加载
try:
    net = ml.Model('trained.tflite', load_to_fb = uos.stat('trained.tflite')[6] > (gc.mem_free() - (64 * 1024))) # type:ignore
except Exception as e:
    raise Exception("Failed to load 'trained.tflite': " + str(e))

try:
    labels = [line.rstrip('\n') for line in open('labels.txt')]
except Exception as e:
    raise Exception("Failed to load 'labels.txt': " + str(e))

# 推进器初始化
MotorHandler.motorInit()

# OpenMV初始化
MVHandler.mvInit()

# PID初始实例化
xPid = PID(1, 1, 0)
hPid = PID(0.01, 0.01, 0)

# 激光传感器初始化
SensorHandler.sensorInit()

# 循环执行部分
while(True):
    image = sensor.snapshot()
    result = net.predict([image])

    if (not result or len(result) <= 0): continue

    MVHandler.clock

    MVHandler.maxSize = 0

    # 自动曝光调整
    MVHandler.autoAdjustExposure(image)

    # LED
    LEDHandler.showCurrentTarget(MVHandler.currentTarget) # 编号[1] = 红色, [2] = 绿色, [3] = 蓝色

    # 渲染当前目标信息
    MVHandler.renderCurrentTargetString(image)
    MVHandler.renderCurrentTargetCount(image)
    MVHandler.renderCurrentBrightness(image)

    # 目标检测
    (scores, maxConfidence, gridX, gridY) = DetectionHandler.analyseResult(result, MVHandler.currentTarget)

    if (maxConfidence >= MVHandler.minConfidence):
        (leftX, leftY, w, h, pixels, centerX, centerY, rotation) = DetectionHandler.getMaxBlob(image, scores, gridX, gridY)
        MVHandler.maxBlob = [leftX, leftY, w, h, pixels, centerX, centerY, 0]
        MVHandler.maxSize = pixels

        image.draw_circle((centerX, centerY, 12), color=ColorsHandler.circleColors[MVHandler.currentTarget], thickness=2)

    # # 手动控制逻辑
    # if (not MotorHandler.isAutoControl):
    #     MotorHandler.leftCtrl = MotorHandler.linearMap(data[1], 110, 200, 5, 10) if (data[1] != 0 and data[2] != 0) else 7.5
    #     MotorHandler.rightCtrl = MotorHandler.linearMap(data[2], 110, 200, 5, 10) if (data[1] != 0 and data[2] != 0) else 7.5

    #     MotorHandler.setMotorSpeed(MotorHandler.leftCtrl, MotorHandler.rightCtrl)
    #     TimeHandler.updateLastTimeWhenNotAutoControl()
    #     continue

    # 未检测到目标或目标过小
    if (MVHandler.maxSize == 0 or BlobHandler.getPixels(MVHandler.maxBlob) <= 50): 
        MotorHandler.UART3.write('a755b725c')
        continue

    # 自动控制逻辑
    # 计算水平(xError)误差
    xError = math.floor(BlobHandler.getX(MVHandler.maxBlob) + BlobHandler.getW(MVHandler.maxBlob) / 2 - image.width() / 2)
    hError = BlobHandler.getPixels(MVHandler.maxBlob) - ColorsHandler.sizeThreshold

    # 计算水平(xOutput)及距离控制量绝对值(hOutput)
    xOutput = xPid.get_pid(xError, 1)
    hOutput = hPid.get_pid(hError, 1)

    # 差动驱动控制
    MotorHandler.leftOut = min(500, -xOutput - hOutput)
    MotorHandler.rightOut = min(500, xOutput - hOutput)

    # 计算映射后的实际电机速度
    MotorHandler.mappedA = MotorHandler.linearMap(MotorHandler.leftOut, 0, 500, 7.7, 8.5)
    MotorHandler.mappedB = MotorHandler.linearMap(MotorHandler.rightOut, 0, 500, 7.7, 8.5)

    image.draw_rectangle(MVHandler.maxBlob[0 : 4], color = (255, 0, 0))
    MotorHandler.UART3.write(f'a{ MotorHandler.mappedA }b{ MotorHandler.mappedB }c')
    
    # 读取激光传感器数据
    if (SensorHandler.UART1.any()):
        sensorData = SensorHandler.readFrame()

        if (sensorData):
            SensorHandler.updateTouchCount(sensorData)