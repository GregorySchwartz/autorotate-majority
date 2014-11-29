#!/usr/bin/env python

# Script for auto rotation of tablet PC
# Modified to work based on majority rule

# From https://wiki.archlinux.org/index.php/Tablet_PC#Auto_Rotation
# Modifications by Gregory W. Schwartz

from time import sleep
from os import path as op
import sys
from subprocess import check_call, check_output
from glob import glob


def bdopen(fname):
    return open(op.join(basedir, fname))


def read(fname):
    return bdopen(fname).read()


for basedir in glob('/sys/bus/iio/devices/iio:device*'):
    if 'accel' in read('name'):
        break
else:
    sys.stderr.write("Can't find an accellerator device!\n")
    sys.exit(1)


devices = check_output(['xinput', '--list', '--name-only']).splitlines()

touchscreen_names = ['touchscreen', 'wacom']
touchscreens = [i for i in devices if any(j in i.lower() for j in touchscreen_names)]

disable_touchpads = True

touchpad_names = ['touchpad', 'trackpoint']
touchpads = [i for i in devices if any(j in i.lower() for j in touchpad_names)]

scale = float(read('in_accel_scale'))

g = 30.0  # (m^2 / s) sensibility, gravity trigger

STATES = [
    {'rot': 'normal', 'coord': '1 0 0 0 1 0 0 0 1', 'touchpad': 'enable',
     'check': lambda x, y: y >= g and x <= g},
    {'rot': 'inverted', 'coord': '-1 0 1 0 -1 1 0 0 1', 'touchpad': 'disable',
     'check': lambda x, y: y <= g and x >= g},
    {'rot': 'left', 'coord': '0 -1 1 1 0 0 0 0 1', 'touchpad': 'disable',
     'check': lambda x, y: x <= g and y <= g},
    {'rot': 'right', 'coord': '0 1 0 -1 0 1 0 0 1', 'touchpad': 'disable',
     'check': lambda x, y: x >= g and y >= g},
]


def rotate(state):
    s = STATES[state]
    check_call(['xrandr', '-o', s['rot']])
    for dev in touchscreens if disable_touchpads else (touchscreens + touchpads):
        check_call([
            'xinput', 'set-prop', dev,
            'Coordinate Transformation Matrix',
        ] + s['coord'].split())
    if disable_touchpads:
        for dev in touchpads:
            check_call(['xinput', s['touchpad'], dev])


def read_accel(fp):
    fp.seek(0)
    return float(fp.read()) * scale


if __name__ == '__main__':

    accel_x = bdopen('in_accel_x_raw')
    accel_y = bdopen('in_accel_y_raw')

    acc = []
    past = None
    while True:
        x = read_accel(accel_x)
        y = read_accel(accel_y)
        for i in range(4):
            if STATES[i]['check'](x, y):
                acc += [i]
                break
        if len(acc) > 4:
            majority = max(set(acc), key=acc.count)
            acc = []
            if majority == past:
                sleep(5)
            else:
                rotate(majority)
