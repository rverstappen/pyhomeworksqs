"""
Test Homeworks QS interface.

Ron Verstappen - 2021 - Kauai
"""
import time
import logging
from pyhomeworksqs.pyhomeworksqs import HomeworksQs

logging.basicConfig(level=logging.DEBUG)

def callback(msg, args):
    """Show the message and arguments."""
    print(msg, args)


print("Starting interface")
hw = HomeworksQs('192.168.189.24', 23, callback)

print("Connected. Waiting for messages.")
hw.run()
time.sleep(10.)

print("Closing.")
hw.close()

print("Done.")
