from pyb import Pin, Timer #type:ignore

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
        TurbineHelper.inverseLeft = inverseLeft
        TurbineHelper.inverseRight = inverseRight

        #高低电平初始化
        self.ain1.low()
        self.ain2.low()
        self.bin1.low()
        self.bin2.low()

        #信号输出暂停时间初始化
        self.ch1.pulse_width_percent(0)
        self.ch2.pulse_width_percent(0)

    #设置舵机左右电机的速度
    @classmethod
    def run(cls, leftSpeed: float | int, rightSpeed: float | int):
        leftSpeed = -leftSpeed if cls.inverseLeft else leftSpeed
        rightSpeed = -rightSpeed if cls.inverseRight else rightSpeed

        #设置左侧电机高低电平
        if leftSpeed < 0:
            cls.ain1.low()
            cls.ain2.high()
        else:
            cls.ain1.high()
            cls.ain2.low()

        #设置右侧电机高低电平
        if rightSpeed < 0:
            cls.bin1.low()
            cls.bin2.high()
        else:
            cls.bin1.high()
            cls.bin2.low()

        #计算左轮PWM脉冲宽度
        leftPulseWith = int(abs(leftSpeed) * cls.period / 100)
        cls.ch1.pulse_width(leftPulseWith)

        #计算右轮PWM脉冲宽度
        rightPulseWith = int(abs(rightSpeed) * cls.period / 100)
        cls.ch2.pulse_width(rightPulseWith)