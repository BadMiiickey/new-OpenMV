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

lastNnUpdateTime: int = time.ticks_ms() # type: ignore
lastAction: str = 'SEARCHING'

NN_UPDATE_INTERVAL_MS: int = 200

# 循环执行部分
while (True):

    # 1. <- 指示当前目标颜色 -> #
    LEDHandler.showCurrentTarget(MVHandler.currentTarget) # 编号[1] = 红色, [2] = 绿色, [3] = 蓝色

    # 2. <- 激光传感器数据处理 -> #
    SensorHandler.processBuffer()

    currentClosestDistance: float = float('inf')
    sensorData: bytes | None = None
    irqState = pyb.disable_irq()
    lastFrame: bytes | None = SensorHandler.lastValidFrame

    pyb.enable_irq(irqState)

    if (lastFrame):
        currentClosestDistance = SensorHandler.getClosestDistance(lastFrame)

    # 3. <- 神经网络处理与决策 -> #
    if (time.ticks_diff(time.ticks_ms(), lastNnUpdateTime) < NN_UPDATE_INTERVAL_MS): continue # type: ignore

    image = sensor.snapshot() # 获取当前帧的图像
    result = net.predict([image]) # 进行神经网络预测
    averageX: int = image.width() // 2 # 加权平均后的目标x坐标, 默认为图像中心
    lastNnUpdateTime = time.ticks_ms() # 更新上次神经网络处理时间 # type: ignore 

    if (result and len(result) > 0):

        # 状态更新与信息处理
        MVHandler.autoAdjustExposure(image)

        # 目标检测
        (peakConfidence, averageX) = MVHandler.analyseResult(result)
        MVHandler.currentAverageConfidence = peakConfidence

        if (currentClosestDistance < MVHandler.TOUCH_VALID_DISTANCE):
            MVHandler.maxBlob = MVHandler.getMaxBlob(image)
    else:
        MVHandler.resetMaxBlob()
        MVHandler.currentAverageConfidence = 0.0

    # 4. <- 同步状态并做出决策 -> #
    (_, _, _, _, pixels, _, _, _) = MVHandler.maxBlob
    MVHandler.maxSize = pixels

    action: str = MVHandler.updateTargetState(currentClosestDistance, MVHandler.currentAverageConfidence)

    # 5. <- 执行决策 -> #
    if (action == 'TRACKING' and lastAction == 'SEARCHING'):
        MotorHandler.sendMotorCommand(725, 765)

    elif (action == 'SEARCHING'):
        MotorHandler.sendMotorCommand(755, 725)

    elif (action == 'MODIFYING'):
        MotorHandler.sendMotorCommand(680, 680)

    elif (action == 'SWITCHED'):
        MotorHandler.sendMotorCommand(690, 690)
        MVHandler.resetMaxBlob()

    elif (action == 'TRACKING'):

        # 绘制识别结果
        # image.draw_rectangle(MVHandler.maxBlob[0 : 4], color=(255, 0, 0))

        xError: float = image.width() // 2 - averageX # type: ignore
        x: float = MotorHandler.getXOutput(xError)
        h: int = MotorHandler.getHOutput(currentClosestDistance)
        left: int = MotorHandler.getLeftOutput(h, x)
        right: int = MotorHandler.getRightOutput(h, x)

        MotorHandler.sendMotorCommand(left, right)

    lastAction = action

    # print(
    #     f'Action: {action:<10} | '
    #     f'Target: {MVHandler.currentTarget} | '
    #     f'Distance: {currentClosestDistance:<4.0f} | '
    #     f'Confidence: {MVHandler.currentAverageConfidence:<4.2f} | '
    #     f'Size: {MVHandler.maxSize:<5} | '
    #     f'Failures: {MVHandler.consecutiveNnFailures}'
    # )

    # MotorHandler.sendMaxConfidence(MVHandler.currentAverageConfidence)
