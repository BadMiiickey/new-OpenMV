import Helper.AssistantHelper as AssistantHelper
import Helper.ColorsHelper as ColorsHelper
import Helper.DetectionHelper as DetectionHelper
import Helper.MVHelper as MVHelper
import Helper.PIDHelper as PIDHelper
import Helper.TimeHelper as TimeHelper
import Helper.TurbineHelper as TurbineHelper
import sensor, time, pyb, tf, uos, gc, math #type:ignore

from Helper.AssistantHelper import AssistantHelper
from Helper.ColorsHelper import ColorsHelper
from Helper.DetectionHelper import DetectionHelper
from Helper.MVHelper import MVHelper
from Helper.PIDHelper import PIDHelper
from Helper.TimeHelper import TimeHelper
from Helper.TurbineHelper import TurbineHelper
from pyb import UART #type:ignore

try:
    net = tf.load("trained.tflite", load_to_fb = uos.stat('trained.tflite')[6] > (gc.mem_free() - (64 * 1024))) #type:ignore
except Exception as e:
    raise Exception('Failed to load "trained.tflite", did you copy the .tflite and labels.txt file onto the mass-storage device? (' + str(e) + ')')

try:
    labels = [line.rstrip('\n') for line in open("labels.txt")]
except Exception as e:
    raise Exception('Failed to load "labels.txt", did you copy the .tflite and labels.txt file onto the mass-storage device? (' + str(e) + ')')

#涡轮初始化
TurbineHelper(inverseLeft = False, inverseRight = False)
TurbineHelper.run(7.5, 7.5)
time.sleep(3)
TurbineHelper.run(8.5, 8.5)
time.sleep(3)

#OpenMV初始化
MVHelper.mvInit()

clock = time.clock() #type:ignore
uart3 = UART(3, 115200)
uart3.init(115200, 8, None, 1)

#颜色阈值导入
circleColors = ColorsHelper().circleColors
redThreshold = ColorsHelper().redThreshold
yellowThreshold = ColorsHelper().yellowThreshold
blackThreshold = ColorsHelper().blackThreshold

sizeThreshold = 10000

xPid = PIDHelper(1, 1, 0, 100)
hPid = PIDHelper(0.01, 0.01, 0, 100)
detectionHelper = DetectionHelper(0)
lastTime = 0
movementSequenceEnabled = False
isAutoControl = True

while(True):
    clock.tick()
    img = sensor.snapshot()
    maxSize = 0
    minConfidence = 0.8 if (MVHelper.flagFind == 3) else 0.97

    MVHelper.renderCurrentTargetString()

    for keyIndex, valueList in enumerate(net.detect(img, thresholds = [(math.ceil(minConfidence * 255), 255)])):
        if (keyIndex == 0): continue
        if (len(valueList) == 0): 
            key = (keyIndex, MVHelper.flagFind)

            if (key in DetectionHelper.detectionMap):
                MVHelper.maxSize = 0
            
            continue

        for value in valueList:
            myBlob = value.rect()
            centerX = math.floor(myBlob.x() + myBlob.w() / 2) #type:ignore
            centerY = math.floor(myBlob.y() + myBlob.h() / 2) #type:ignore

            img.draw_circle((centerX, centerY, 12), color = circleColors[keyIndex], thickness = 2)
            
            key = (keyIndex, MVHelper.flagFind)

            if (key in DetectionHelper.detectionMap):
                targetType = DetectionHelper.detectionMap[key]

                img.draw_string(10, 10, targetType + '!')

                detectionHelper.myCount = MVHelper.stateTransform(img, myBlob, detectionHelper.myCount, targetType)

    #读取串口
    if (uart3.any()):
        data = uart3.read()

        if (len(data) == 0): continue
        if (
            data[0] == 0xA5
            and data[3] == 0x5A
            and data[1] != 0
            and data[2] != 0
        ):
            isAutoControl = False

            if (not movementSequenceEnabled): continue

            TurbineHelper.run(7.4, 7.4)
            time.sleep_ms(5000) #type:ignore
            TimeHelper.delayWithStartAction(8000, lambda: TurbineHelper.run(8.5, 8.5))
            movementSequenceEnabled = False

    #手动控制逻辑
    if (not isAutoControl):
        leftCtrl = AssistantHelper.mapValue(data[1], 110, 200, 5, 10) if (data[1] != 0 and data[2] != 0) else 7.4
        rightCtrl = AssistantHelper.mapValue(data[2], 110, 200, 5, 10) if (data[1] != 0 and data[2] != 0) else 7.4

        TurbineHelper.run(leftCtrl, rightCtrl)

        print('leftCtrl:', leftCtrl)
        print('rightCtrl:', rightCtrl)

        timeData = pyb.millis()

        if (timeData - lastTime > 2000):
            lastTime = timeData
            isAutoControl = True

        continue

    #未检测到目标
    if (MVHelper.maxSize == 0):
        TurbineHelper.run(7.55, 7.25)
        continue

    #忽略过小目标
    if (MVHelper.maxBlob.w() * MVHelper.maxBlob.h() <= 100): continue #type:ignore

    #自动控制逻辑
    xError = math.floor(MVHelper.maxBlob[0] + MVHelper.maxBlob.w() / 2 - img.width() / 2) #type:ignore
    hError = MVHelper.maxBlob.w() * MVHelper.maxBlob.h() - sizeThreshold #type:ignore
    xOutput = xPid.getPid(xError, 1)
    hOutput = hPid.getPid(hError, 1)
    leftOut = min(500, -xOutput - hOutput)
    rightOut = min(500, xOutput - hOutput)
    mappedA = AssistantHelper.mapValue(leftOut, 0, 500, 7.7, 8.5)
    mappedB = AssistantHelper.mapValue(rightOut, 0, 500, 7.7, 8.5)

    img.draw_rectangle(MVHelper.maxBlob[0 : 4], color = (255, 0, 0))
    TurbineHelper.run(mappedA, mappedB)

    print("leftOut:", leftOut)
    print("rightOut:", rightOut)
    print("mappedA:", mappedA)
    print("mappedB:", mappedB)

    timeData = pyb.millis()
    
    if (timeData - lastTime > 2000):
        lastTime = timeData