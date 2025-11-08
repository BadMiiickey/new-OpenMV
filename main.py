import sensor, ml, uos, gc, pyb, time # type: ignore

from core.LEDHandler import LEDHandler
from core.MVHandler import MVHandler
from core.MotorHandler import MotorHandler
from core.SensorHandler import SensorHandler

# 机器学习文件加载
try:
    net = ml.Model(
        'trained.tflite', 
        load_to_fb=uos.stat('trained.tflite')[6] > (gc.mem_free() - (64 * 1024)) # type: ignore
    )
except Exception as e:
    raise Exception('Failed to load trained.tflite: ' + str(e))

try:
    labels = [line.rstrip('\n') for line in open('labels.txt')]
except Exception as e:
    raise Exception('Failed to load labels.txt: ' + str(e))

MotorHandler.motorInit() # 推进器初始化
MVHandler.mvInit() # OpenMV初始化
SensorHandler.sensorInit() # 激光传感器初始化

isSwitching: bool = False
lastNnUpdateTime: int = time.ticks_ms() # type: ignore

NN_UPDATE_INTERVAL_MS: int = 200

# 循环执行部分
while(True):
    LEDHandler.showCurrentTarget(MVHandler.currentTarget) # 编号[1] = 红色, [2] = 绿色, [3] = 蓝色
    
    # 获取基础数据
    SensorHandler.processBuffer()

    currentClosestDistance: float = float('inf')
    sensorData: bytes | None = None
    irqState = pyb.disable_irq()
    lastFrame: bytes | None = SensorHandler.lastValidFrame
    sensorData = lastFrame if (lastFrame) else None

    pyb.enable_irq(irqState)

    if (sensorData):
        currentClosestDistance = SensorHandler.getClosestDistance(sensorData)

    if (isSwitching or time.ticks_diff(time.ticks_ms(), lastNnUpdateTime) >= NN_UPDATE_INTERVAL_MS): # type: ignore
        lastNnUpdateTime = time.ticks_ms() # type: ignore

        image = sensor.snapshot()
        result = net.predict([image])

        if (result and len(result) > 0):
            # 状态更新与信息处理
            MVHandler.autoAdjustExposure(image)
            # MVHandler.renderCurrentTarget(image)
            # MVHandler.renderCurrentBrightness(image)

            # 目标检测
            (scores, averageConfidence, averageX, averageY) = MVHandler.analyseResult(result)
            MVHandler.maxBlob = MVHandler.getMaxBlob(image, scores, averageX, averageY, currentClosestDistance)
            MVHandler.currentAverageConfidence = averageConfidence
        else:
            MVHandler.resetMaxBlob()
            MVHandler.currentAverageConfidence = 0.0
    
    (_, _, _, _, pixels, centerX, _, _) = MVHandler.maxBlob
    MVHandler.maxSize = pixels

    # MotorHandler.sendMaxConfidence(maxConfidence) # 发送最大置信度至STM32

    print(f'Closest Distance: {currentClosestDistance} mm, \
          Average Confidence: {MVHandler.currentAverageConfidence}, \
          Max Size: {MVHandler.maxSize}')
    # 获取当前决策
    if (isSwitching):
        MotorHandler.sendMotorCommand(670, 670)
        action: str = 'ASYNC'
    else:
        action: str = MVHandler.updateTargetState(currentClosestDistance, MVHandler.currentAverageConfidence)
    
    # 执行当前决策
    if (action == 'SEARCHING'):
        MotorHandler.sendMotorCommand(755, 725)

    elif (action == 'MODIFYING'):
        MotorHandler.sendMotorCommand(680, 680)

    elif (action == 'SWITCHED'):
        MVHandler.resetMaxBlob() # 切换目标后重置最大目标信息
        isSwitching = True
        MotorHandler.sendMotorCommand(690, 690)

    elif (action == 'TRACKING'):
        # 绘制识别结果
        # image.draw_circle((centerX, centerY, 12), color=MVHandler.CIRCLE_COLORS[MVHandler.currentTarget], thickness=2)
        # image.draw_rectangle(MVHandler.maxBlob[0 : 4], color=(255, 0, 0))
        
        # 计算误差与PID输出
        xError: float = image.width() // 2 - centerX # type: ignore

        # 计算PID输出
        x: float = MotorHandler.getXOutput(xError, MVHandler.maxSize)
        h: int = MotorHandler.getHOutput(currentClosestDistance)

        # 计算左右轮输出
        left: int = MotorHandler.getLeftOutput(h, x)
        right: int = MotorHandler.getRightOutput(h, x)

        MotorHandler.sendMotorCommand(left, right)