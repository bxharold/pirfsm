# pirfsm
4-state FSM to control PIR-activated camera.

4-state FSM for PIR; button_press:long/short (see fsm.py) 
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
