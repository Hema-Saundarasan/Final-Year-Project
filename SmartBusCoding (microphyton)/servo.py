#-----------HEMA SAUNDARASAN
#--------------52224123036

#servo.py

from machine import PWM, Pin

class Servo:
    def __init__(self, pin, freq=50):
        self.pwm = PWM(pin, freq=freq)

    def write_angle(self, angle):
        min_us = 500
        max_us = 2500
        duty = int(min_us + (angle/180)*(max_us-min_us))
        self.pwm.duty_u16(int(duty/20000*65535))
