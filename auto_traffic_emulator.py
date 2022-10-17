# this script is necessary in order to run the SAME simulation (in terms of traffic flows)
# it focuses the mininet emulator window and inputs the commands to run iperf
# and other connections between hosts in the network

import pygetwindow as gw
import pyautogui as pag
from pyautogui import press, typewrite, hotkey
import pydirectinput
import time
import os


def ampersand(): #pydirectinput non conosce &
    pydirectinput.keyDown('shift')
    pydirectinput.press('6')
    pydirectinput.keyUp('shift')

def trattinobasso():
    pydirectinput.keyDown('shift')
    pydirectinput.press("-")
    pydirectinput.keyUp('shift')


def mininet_cmd(command):
    # pydirectinput inserisce input da tastiera inglese, quindi quello che per lui è /, per me è -
    command = command.replace('-', '/')
    #command = command.replace('_', '?')
    
    for i in range(len(command)):
        if command[i].isupper():
            pydirectinput.keyDown('shift')
            pydirectinput.press(command[i].lower())
            pydirectinput.keyUp('shift')
            continue
        if command[i] == '&':
            ampersand()
            continue
        if command[i] == '_':
            trattinobasso()
            continue
        pydirectinput.press(command[i])

    pydirectinput.press('enter')


pydirectinput.PAUSE=0.01


win = gw.getWindowsWithTitle('comnetsemu')[0]
try:
    win.activate()
except gw.PyGetWindowException:
    pass

time.sleep(1)
pydirectinput.press('enter')
mininet_cmd("source shpy.py")
pydirectinput.press('enter')
'''
time.sleep(4)
mininet_cmd("h1 iperf -c 10.0.0.100 -n 10M -i2 &")


time.sleep(1)
mininet_cmd("srv iperf -c 10.0.0.1 -n 1500M -i2 &")

time.sleep(8)

mininet_cmd("h2 iperf -c 10.0.0.4 -n 1000M -i2 &")
time.sleep(4)
mininet_cmd("h7 iperf -c 10.0.0.3 -n 800M -i2 &")

time.sleep(17)

mininet_cmd("srv iperf -c 10.0.0.1 -n 1500M -i2 &")

time.sleep(5)

mininet_cmd("srv iperf -c 10.0.0.6 -n 1500M -i2 &")

mininet_cmd("h1 iperf -c 10.0.0.3 -n 1300M -i2 &")
time.sleep(3)
mininet_cmd("h3 iperf -c 10.0.0.1 -n 250M -i2 &")
mininet_cmd("srv iperf -c 10.0.0.6 -n 2500M -i2 &")

time.sleep(34)

mininet_cmd("h2 iperf -c 10.0.0.6 -n 100M -i2 &")
time.sleep(3)
mininet_cmd("h6 iperf -c 10.0.0.2 -n 850M -i2 &")

time.sleep(5)

mininet_cmd("srv iperf -c 10.0.0.1 -n 1500M -i2 &")

time.sleep(5)

mininet_cmd("srv iperf -c 10.0.0.6 -n 1500M -i2 &")

mininet_cmd("h1 iperf -c 10.0.0.3 -n 1300M -i2 &")
time.sleep(1)
mininet_cmd("h3 iperf -c 10.0.0.1 -n 250M -i2 &")
mininet_cmd("srv iperf -c 10.0.0.5 -n 2500M -i2 &")
'''