# ---------------------------------------------------------------------
# A script to put VESNA device in reset state
# ---------------------------------------------------------------------

import sys
import os

class vesna_reset():

    def __init__(self):
        # Export GPIO2_2 or linuxPin-66 to user space 
        try:
            os.system('echo 66 > /sys/class/gpio/export')
        except:
            print("Pin already exported")
        
        # Set the direction of the pin to output
        os.system('echo out > /sys/class/gpio/gpio66/direction')
        return

    def reset(self):
        # Set the value to 0 - reset Vesna
        os.system('echo 0 > /sys/class/gpio/gpio66/value')
        return

    def wakeup(self):
        # Set value back to 1 - wake Vesna up
        os.system('echo 1 > /sys/class/gpio/gpio66/value')
        return


if __name__ == '__main__':

    vesna = vesna_reset()
    
    if (int(sys.argv[1]) == 0):
        vesna.reset()
    else:
        vesna.wakeup()
        

