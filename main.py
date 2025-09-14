import sensor, ml, uos, gc # type: ignore

from core.LEDHandler import LEDHandler
from core.MVHandler import MVHandler
from core.MotorHandler import MotorHandler
from core.SensorHandler import SensorHandler

# 机器学习文件加载
try:
    net = ml.Model(
        'trained.tflite', 
        load_to_fb = uos.stat('trained.tflite')[6] > (gc.mem_free() - (64 * 1024)) # type: ignore
    )
except Exception as e:
    raise Exception("Failed to load 'trained.tflite': " + str(e))

try:
    labels = [line.rstrip('\n') for line in open('labels.txt')]
except Exception as e:
    raise Exception("Failed to load 'labels.txt': " + str(e))

MotorHandler.motorInit() # 推进器初始化
MVHandler.mvInit() # OpenMV初始化
SensorHandler.sensorInit() # 激光传感器初始化

# 循环执行部分
while(True):
    gc.enable()

    # 读取激光传感器数据
    if (not SensorHandler.UART1.any()): continue

    sensorData = SensorHandler.readFrame()

    if (not sensorData): continue
    
    # 获取基础数据
    closestDistanceThisFrame = SensorHandler.getClosestDistance(sensorData)
    image = sensor.snapshot()
    result = net.predict([image])

    if (not result or len(result) <= 0): continue

    # 状态更新与信息处理
    MVHandler.resetMaxBlob()
    MVHandler.autoAdjustExposure(image)
    MVHandler.renderCurrentTarget(image)
    MVHandler.renderCurrentBrightness(image)
    LEDHandler.showCurrentTarget(MVHandler.currentTarget) # 编号[1] = 红色, [2] = 绿色, [3] = 蓝色

    # 目标检测
    (scores, maxConfidence, gridX, gridY) = MVHandler.analyseResult(result)
    (x, y, w, h, pixels, centerX, centerY, rotation) = MVHandler.getMaxBlob(image, scores, gridX, gridY)
    MVHandler.maxBlob = [x, y, w, h, pixels, centerX, centerY, rotation]
    MVHandler.maxSize = pixels

    # 获取当前决策
    action = MVHandler.updateTargetState(closestDistanceThisFrame, maxConfidence)
    
    # 执行当前决策
    if (action == 'SWITCHED' or action == 'SEARCHING'):
        MotorHandler.UART3.write('a755b715c')

    elif (action == 'TRACKING'):

        # 绘制识别结果
        image.draw_circle((centerX, centerY, 12), color=MVHandler.CIRCLE_COLORS[MVHandler.currentTarget], thickness=2)
        image.draw_rectangle(MVHandler.maxBlob[0 : 4], color=(255, 0, 0))
        
        # 计算误差与PID输出
        xError = image.width() / 2 - centerX

        # 计算PID输出
        xOutput = MotorHandler.xPid.get_pid(xError, 1)
        hOutput = MotorHandler.CRUISE_SPEED if (closestDistanceThisFrame > MotorHandler.BRAKE_DISTANCE) else -50

        # 计算左右轮输出
        leftOut = max(-500, min(500, hOutput + xOutput))
        rightOut = max(-500, min(500, hOutput - xOutput))

        # 线性映射输出到电机
        mappedA = MotorHandler.linearMap(leftOut, -500, 500, 5, 10)
        mappedB = MotorHandler.linearMap(rightOut, -500, 500, 5, 10)

        MotorHandler.UART3.write(f'a{mappedA:03d}b{mappedB:03d}c')

    gc.collect()