#!/usr/bin/python3
"""
pi@mc21a:~/pi/pirfsm.py  
4-state FSM for PIR; button_press:long/short(see a.py, b.py, fsm.py) 
LEDs show state: ready to start detection, waiting for motion, snapshot

Controller calls a state process which does its thing (turn on LEDs)
including polling to see if there was a state-change input.
State returns the reason it returned to the controller, 
and the controller does a simple lookup to determine the next state.
"if curState=X and input=Y, then nextState = Z."
Polling is done by checking a global vbl (msg). If it's been set
(in this version, by the button handler) then return to the controller.


                 Start <---------- Snap(~Blue) 
              (~~yellow)   Long*    |^          
                  |                 ||
                  |Short            ||Short(will be motion detected)
                  |             auto||
                  v      Auto       |v
                Warm ------------> Ready
             (~Yellow)             (Red) 

    *Long from any state goes to start... except when adding PIR.
"""

from gpiozero import MotionSensor
from picamera import PiCamera
import time
import datetime
from signal import pause
from gpiozero import LED, Button
ledb = LED(13)
ledy = LED(19)
ledr = LED(26)
button = Button(6)
shortPressTime, longPressTime, curState = 0.1, 1.2, "start"  # globals

states = ['start','warm','ready','snap']
messages = ['shortPress', 'longPress','null']

pir = MotionSensor(17)  # PIR Sensor is using GPIO-17 (Pin 11)
camera = PiCamera()
 
def getFileName():   # create new Filename from date and time
    return datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.jpg")

def setLED(ryb):
    ledr.on() if ryb[0]=="R" else ledr.off()
    ledy.on() if ryb[1]=="Y" else ledy.off()
    ledb.on() if ryb[2]=="B" else ledb.off()
        
def flashLED(ryb, ontime, offtime):
    setLED(ryb)
    time.sleep(ontime)
    setLED("ryb")
    time.sleep(offtime)
    
msg = ""  # incoming message from BGH
cur = ""  
def startState():
    global msg
    cur = "start"
    setLED("ryb")
    print(f"in {cur}, incoming={msg}    # calm yellow flash, wait for button")
    msg = ""
    while True:
        flashLED("rYb", 0.6, 0.4)    # calm yellow flash, wait for button
        if msg != "":
            print(f"{cur} got a message: {msg}")
            return [cur,msg]
        else:
            print(" s", end="")

def warmState():
    global msg
    cur = "warm"
    setLED("rYb")
    print(f"in {cur}, incoming={msg}   # quicker yellow flash, warming up")
    msg = "null"
    for i in range(10):   # give me time to get out of the way after button press
        flashLED("rYb", 0.25, 0.25)   # quicker yellow flash, warming up
    return[cur,msg]

def readyState():
    global msg
    cur = "ready"
    setLED("Ryb")            # no flash, red means ready 
    print(f"in {cur}, incoming={msg}   # no flash, red means ready")
    pir.wait_for_motion()     # Button-press does not interrupt this.
    msg = 'shortPress'
    return [cur,msg]

def snapState():
    global msg
    cur = "snap"
    setLED("ryB")
    print(f"in {cur}, incoming={msg}   # flashing blue means taking picture")
    msg = "null"
    filename = getFileName()
    print(f"Sneaky Person Alert!! {getFileName()} ")
    camera.start_preview() # Preview camera on screen 
    camera.capture(filename) # Take a picture of intruder
    camera.stop_preview()
    #time.sleep(10) # may be needed, but reasonable. Use blue-blink instead.
    for i in range(19):
        flashLED("ryB", 0.15, 0.35)  # flashing blue means taking picture
    setLED("ryb")
    return[cur,msg]

b_t0, b_tf, b_downtime, msg = 0.0,0.0,0.0, "incoming message"
def buttonPressStart():
    global b_t0
    b_t0 = time.time()

def buttonReleased():
    global b_t0, msg
    b_tf = time.time()
    #print(f'Button was released at {(b_tf%1000):.2f}, held for {(b_tf-b_t0):.2f}')
    b_downtime = b_tf - b_t0
    b_t0, b_tf = 0,0
    if b_downtime > longPressTime:     
        msg = 'longPress'
    elif b_downtime > shortPressTime:  
        msg = 'shortPress'
    else:                              
        msg = 'noPress'          
    print(msg)
    
button.when_pressed = buttonPressStart
button.when_released = buttonReleased

def jump(tpl):
    curState,message = tpl
    print (f"\njump from {curState}, message={message}")
    if   [curState, message] == ['start','START']:       tpl = startState()
    elif [curState, message] == ['start','shortPress']:  tpl = warmState()
    elif [curState, message] == ['start','longPress']:   tpl = startState()
    elif [curState, message] == ['warm','null']:         tpl = readyState()
    elif [curState, message] == ['warm','shortPress']:   tpl = startState()
    elif [curState, message] == ['warm','longPress']:    tpl = startState()
    elif [curState, message] == ['ready','shortPress']:  tpl = snapState()
    elif [curState, message] == ['ready','longPress']:   tpl = startState()
    elif [curState, message] == ['snap','longPress']:    tpl = startState()
    elif [curState, message] == ['snap','null']:         tpl = readyState()
    else:
        print(f"Unhandled {tpl} at {(time.time()%1000):.2f}")
        time.sleep(2)
        return ['start','START']
    return tpl  

def main():
    global msg
    setLED("ryb")
    time.sleep(1)
    cur = 'start'
    jump([cur,'START'])
    while True:    
        [cur,msg] = jump([cur,msg])
        
main()

