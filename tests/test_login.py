"""
Test Homeworks QS interface.

Ron Verstappen - 2021 - Kauai
"""
import time
import logging
from pyhomeworksqs.pyhomeworksqs import HomeworksQs

#logging.basicConfig(level=logging.DEBUG)

def callback(msg, iid, args):
    """Show the message and arguments."""
    print(msg, iid, args)


print("Starting interface")
hw = HomeworksQs('192.168.189.24', 23, callback)

print("Connected. Waiting for messages.")
#hw.run()
time.sleep(5.)
hw.set_dimmer_level(103,50.0,0,0)
time.sleep(5.)
hw.set_dimmer_level(103,100.0,0,0)
time.sleep(5.)
hw.set_dimmer_level(103,0.0,0,0)
time.sleep(5.)

print("Closing.")
hw.close()

print("Done.")
