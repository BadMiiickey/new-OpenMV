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

X_MODE_CHANGE_DISTANCE: int = 400 # 转向x坐标采样模式切换距离(单位mm)

# 循环执行部分
while (True):

    # 1. <- 指示当前目标颜色 -> #
    LEDHandler.showCurrentTarget(MVHandler.currentTarget) # 编号[1] = 红色, [2] = 绿色, [3] = 蓝色

    # 2. <- 激光传感器数据处理 -> #
    SensorHandler.processBuffer()

    currentClosestDistance: float = float('inf')
    irqState: int = pyb.disable_irq()
    lastFrame: bytes | None = SensorHandler.lastValidFrame

    pyb.enable_irq(irqState)

    if (lastFrame):
        currentClosestDistance = SensorHandler.getClosestDistance(lastFrame)

    # 3. <- 神经网络处理与决策 -> #
    image: sensor.image = sensor.snapshot() # 获取当前帧的图像
    result: list = net.predict([image]) # 进行神经网络预测
    averageX: int = image.width() // 2 # 加权平均后的目标x坐标, 默认为图像中心

    if (result and len(result) > 0):
        # MVHandler.autoAdjustExposure(image, MVHandler.maxBlob[0:4]) # 自动曝光调整

        (peakConfidence, averageX) = MVHandler.analyseResult(result) # 分析神经网络输出结果
        MVHandler.currentAverageConfidence = peakConfidence # 更新当前平均置信度

        if (currentClosestDistance < MVHandler.TOUCH_VALID_DISTANCE):
            MVHandler.maxBlob = MVHandler.getMaxBlob(image)
    else:
        MVHandler.resetMaxBlob()
        MVHandler.currentAverageConfidence = 0.0

    # 4. <- 同步状态并做出决策 -> #
    (_, _, _, _, pixels, _, _, _) = MVHandler.maxBlob
    MVHandler.maxSize = pixels # 更新当前最大目标面积

    action: str = MVHandler.updateTargetState(currentClosestDistance, MVHandler.currentAverageConfidence)

    # 5. <- 执行决策 -> #
    if (action == 'SEARCHING'):
        MotorHandler.sendMotorCommand(755, 725)

    # elif (action == 'MODIFYING'):
    #     MotorHandler.sendMotorCommand(680, 680) # 室内可用

    elif (action == 'SWITCHED'):
        MotorHandler.sendMotorCommand(690, 690)
        MVHandler.resetMaxBlob()

    elif (action == 'TRACKING'):

        # 绘制识别结果
        # image.draw_rectangle(MVHandler.maxBlob[0:4], color=(255, 0, 0))
        
        xError: float = image.width() // 2 - averageX # type: ignore
        x: float = MotorHandler.getXOutput(xError)
        h: int = 180
        left: int = MotorHandler.getLeftOutput(h, x)
        right: int = MotorHandler.getRightOutput(h, x)

        MotorHandler.sendMotorCommand(left, right)

    # print(
    #     f'Action: {action:<10} | '
    #     f'Target: {MVHandler.currentTarget} | '
    #     f'Distance: {currentClosestDistance:<4.0f} | '
    #     f'Confidence: {MVHandler.currentAverageConfidence:<4.2f} | '
    #     f'Size: {MVHandler.maxSize:<5} | '
    # )

    # MotorHandler.sendMaxConfidence(MVHandler.currentAverageConfidence)
