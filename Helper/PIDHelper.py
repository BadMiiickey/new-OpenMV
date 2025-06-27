from pyb import millis
from math import pi, isnan

class PIDHelper:
    kp = 0
    ki = 0
    kd = 0
    integrator = 0
    imax = 0
    lastError = 0
    lastDerivative = 0
    lastT = 0
    RC = 1 / (2 * pi * 20)

    def __init__(self, kp: float | int, ki: float | int, kd: float | int, imax: float | int):
        self.kp = float(kp)
        self.ki = float(ki)
        self.kd = float(kd)
        self.imax = float(imax)
        self.lastDerivative = float('NaN')

    def getPid(self, error: float | int, scaler: float | int ):
        tNow = millis()
        dt = tNow - self.lastT
        output = 0

        if self.lastT == 0 or dt > 1000:
            dt = 0
            self.resetI()

        self.lastT = tNow
        deltaTime = float(dt) / float(1000)
        output += error * self.kp

        if abs(self.kd) > 0 and dt > 0:
            if isnan(self.lastDerivative):
                derivative = 0
                self.lastDerivative = 0
            else:
                derivative = (error - self.lastError) / deltaTime

            derivative = self.lastDerivative + ((deltaTime / (self.RC + deltaTime)) * (derivative - self.lastDerivative))

            self.lastError = error
            self.lastDerivative = derivative
            output += self.kd * derivative

        output *= scaler

        if abs(self.ki) > 0 and dt > 0:
            self.integrator += (error * self.ki) * scaler * deltaTime

            if self.integrator < -self.imax: self.integrator = -self.imax
            elif self.integrator > self.imax: self.integrator = self.imax
            output += self.integrator

        return output

    def resetI(self):
        self.integrator = 0
        self.lastDerivative = float('NaN')
