import time
import utime
from keypad import KeyPad
from machine import Pin
import time

# put functions here:

def key():
    '''returns key value'''
    keyvalue=keyPad.scan()
    if keyvalue!= None:
        print('Your input:',keyvalue)
        time.sleep_ms(200)
        return keyvalue
    
# boolean to see if someone has escaped
onTheLoose = False

#define pins for keypad
keyPad=KeyPad(14,27,26,25,13,21,22,23)

# for key pad tries and inputs
keyInNum=0
tries = 0


#code that Josiah will provide
keyOut=['1','2','3','4']

#key received
keyIn=['','','','']

patientCurfew = 18

# Get the current time
currentTime = utime.localtime()

# Get only the hour
currentHour = currentTime[3]

print("Current Time:", "{:02d}".format(currentHour))

# oke boolean detect person code:
if personPasses:
# if detects:
    # run romains keypad code
    startTime = time.time()

    while True:
        keydata=key()
        if keydata!=None:
            keyIn[keyInNum]=keydata
            keyInNum=keyInNum+1
            
        if keyInNum==4:
            if keyIn==keyOut:
                print("passWord right!")
                # wait a couple seconds then start checking for person passing by
                # reset pass key in
                keyIn=['','','','']
                break

            else:
                print("passWord error!")
                # have retry logic send message via bluetooth
                tries = tries + 1
                # reset pass key in
                keyIn=['','','','']
                # restart timer for homeowner if they get it wrong
                startTime = time.time()
                
                if tries >= 3:
                    print("Someone is trying to leave the house")
                    #notify the homeowner but don't stop tries
                
            keyInNum=0
        
        currentTime = time.time()
        
        # checking not too much time has been spent since sonor was triggered
        if (currentTime - startTime) >= 10:
            print("Someone has left the house")
            #notify homeowner that someone 
            onTheLoose = True

if onTheLoose:
    # send message to homeowner
    startTimer = time.time()
    