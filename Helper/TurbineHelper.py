from pyb import Pin, Timer

class TurbineHelper:
    inverseLeft = False
    inverseRight = False
    ain1 = Pin('P0', Pin.OUT_PP)
    ain2 = Pin('P1', Pin.OUT_PP)
    bin1 = Pin('P2', Pin.OUT_PP)
    bin2 = Pin('P3', Pin.OUT_PP)
    pwmA = Pin('P7')
    pwmB = Pin('P8')
    tim = Timer(4, freq = 50)
    ch1 = tim.channel(1, Timer.PWM, pin = pwmA)
    ch2 = tim.channel(2, Timer.PWM, pin = pwmB)
    period = tim.period()

    def __init__(self, inverseLeft = False, inverseRight = False):
        self.inverseLeft = inverseLeft
        self.inverseRight = inverseRight

        #高低电平初始化
        self.ain1.low()
        self.ain2.low()
        self.bin1.low()
        self.bin2.low()

        #信号输出暂停时间初始化
        self.ch1.pulse_width_percent(0)
        self.ch2.pulse_width_percent(0)

    @staticmethod
    def run(leftSpeed: float | int, rightSpeed: float | int):
        leftSpeed = -leftSpeed if TurbineHelper.inverseLeft else leftSpeed
        rightSpeed = -rightSpeed if TurbineHelper.inverseRight else rightSpeed

        #设置左侧电机高低电平
        if leftSpeed < 0:
            TurbineHelper.ain1.low()
            TurbineHelper.ain2.high()
        else:
            TurbineHelper.ain1.high()
            TurbineHelper.ain2.low()

        #设置右侧电机高低电平
        if rightSpeed < 0:
            TurbineHelper.bin1.low()
            TurbineHelper.bin2.high()
        else:
            TurbineHelper.bin1.high()
            TurbineHelper.bin2.low()

        #计算左轮PWM脉冲宽度
        leftPulseWith = int(abs(leftSpeed) * TurbineHelper.period / 100)
        TurbineHelper.ch1.pulse_width(leftPulseWith)

        #计算右轮PWM脉冲宽度
        rightPulseWith = int(abs(rightSpeed) * TurbineHelper.period / 100)
        TurbineHelper.ch2.pulse_width(rightPulseWith)
