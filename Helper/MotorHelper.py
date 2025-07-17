from pyb import Pin, Timer #type:ignore

class MotorHelper:
    inverseLeft = False
    inverseRight = False
    
    pwmA = Pin('P7')
    pwmB = Pin('P8')

    tim = Timer(4, freq = 50)
    period = tim.period()

    ch1 = tim.channel(1, Timer.PWM, pin = pwmA)
    ch2 = tim.channel(2, Timer.PWM, pin = pwmB)

    #是否自动控制
    isAutoControl = True

    #手动控制速度
    leftCtrl: int | float | None = None
    rightCtrl: int | float | None = None

    #自动控制相关变量
    leftOut: int | float | None = None
    rightOut: int | float | None = None
    mappedA: int | float | None = None
    mappedB: int | float | None = None

    #电机脉冲宽度
    leftPulseWith: int | float | None = None
    rightPulseWith: int | float | None = None

    #初始化电机
    @classmethod
    def motorInit(cls):

        #信号输出暂停时间初始化
        cls.ch1.pulse_width_percent(0)
        cls.ch2.pulse_width_percent(0)

    #设置舵机左右电机的速度
    @classmethod
    def setMotorSpeed(cls, leftSpeed: float | int, rightSpeed: float | int):
        leftSpeed = -leftSpeed if cls.inverseLeft else leftSpeed
        rightSpeed = -rightSpeed if cls.inverseRight else rightSpeed

        #计算左轮PWM脉冲宽度
        cls.leftPulseWith = int(abs(leftSpeed) * cls.period / 100)
        cls.ch1.pulse_width(cls.leftPulseWith)

        #计算右轮PWM脉冲宽度
        cls.rightPulseWith = int(abs(rightSpeed) * cls.period / 100)
        cls.ch2.pulse_width(cls.rightPulseWith)

    #线性映射
    @staticmethod
    def linearMap(x: float | int, inMin: float | int, inMax: float | int, outMin: float | int, outMax: float | int):
        return (x - inMin) * (outMax - outMin) / (inMax - inMin) + outMin