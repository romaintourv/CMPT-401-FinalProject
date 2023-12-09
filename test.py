from machine import Pin, I2C
import time
from keypad import KeyPad
from micropython import const
from ble_advertising import advertising_payload
import bluetooth
import random
import struct
from I2C_LCD import I2cLcd

############################################################################
# Stuff for bluetooth
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_READ | _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)
class BLESimplePeripheral:
    def __init__(self, ble, name="ESP32"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()   
        self._write_callback = None
        self._payload = advertising_payload(name=name, services=[_UART_UUID])
        self._advertise()

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            print("New connection", conn_handle)
            print("\nThe BLE connection is successful.")
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            print("Disconnected", conn_handle)
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx and self._write_callback:
                self._write_callback(value)

    def send(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_tx, data)

    def is_connected(self):
        return len(self._connections) > 0

    def _advertise(self, interval_us=500000):
        print("Starting advertising")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def on_write(self, callback):
        self._write_callback = callback
#######################################################################################

keyPad = KeyPad(14, 27, 26, 25, 13, 21, 22, 23)

def print_separator(title):
    separator_length = 40
    separator_line = '-' * separator_length
    print("\n" + separator_line)
    print(title.center(separator_length))
    print(separator_line + "\n")

patientInfo = []

def timeDisplay(count, distance):
    if len(devices) == 0:
        print("No i2c device !")
    else:
        for device in devices:
            print("I2C addr: "+hex(device))
            lcd = I2cLcd(i2c, device, 2, 16)

    try:
        lcd.move_to(0, 0)
        lcd.putstr(distance + " meters away")
        
        minutes = count // 60
        seconds = count % 60

        lcd.move_to(0, 1)
        lcd.putstr("Time: {:02d}:{:02d}".format(minutes, seconds))
        time.sleep_ms(1000)

    except:
        pass
    
def displayMain():
    if len(devices) == 0:
        print("No i2c device !")
    else:
        for device in devices:
            print("I2C addr: "+hex(device))
            lcd = I2cLcd(i2c, device, 2, 16)

    try:
        lcd.move_to(0, 0)
        lcd.putstr("MemoryGuard")

        lcd.move_to(0, 1)
        lcd.putstr("BF & SP: Listening")

    except:
        pass
def passDisplay():
    if len(devices) == 0:
        print("No i2c device !")
    else:
        for device in devices:
            print("I2C addr: "+hex(device))
            lcd = I2cLcd(i2c, device, 2, 16)

    try:
        lcd.move_to(0, 0)
        lcd.putstr("Password:")

        lcd.move_to(0, 1)

    except:
        pass

# put functions here:
i2c = I2C(scl=Pin(4), sda=Pin(0), freq=400000)
devices = i2c.scan()

trigPin=Pin(33,Pin.OUT,0)
echoPin=Pin(2,Pin.IN,0)

soundVelocity=340
distance=0
distanceThreshold = 50

# for key pad tries and inputs
keyInNum = 0
tries = 0

# code that Josiah will provide
keyOut = ['1', '2', '3', '4']

# key received
keyIn = ['', '', '', '']

def key():
    '''returns key value'''
    keyvalue = keyPad.scan()
    if keyvalue is not None:
        print('Your input:', keyvalue)
        time.sleep_ms(200)
        return keyvalue

def getSonar():
    trigPin.value(1)
    time.sleep_us(10)
    trigPin.value(0)
    while not echoPin.value():
        pass
    pingStart=time.ticks_us()
    while echoPin.value():
        pass
    pingStop=time.ticks_us()
    pingTime=time.ticks_diff(pingStop,pingStart)
    distance=pingTime*soundVelocity//2//10000
    return int(distance)

print_separator("Instructions")
print("Hello, here are some simple instructions that will help you get started up: ")
print("First you will need to log in to be able to access the Patient page where you will be able to add new patients and view their information.")
print("When adding a new patient you will be prompted with a few questions that will be used to cater our services for each patient.")
print("These questions will include their approximate walking speed, and the times they should be in their room.")

print_separator("Welcome") 
print("\n1. Login")
print("2. Exit")

choice = input("Select an option (1/2): ")

if choice == '1':
    userName = input("Username: ")
    userPassword = input("Password: ")
    
    if userName == "Nurse" and userPassword == "1234":
        print_separator("Patients")
        print("\n1. Add Patient")
        print("2. Patient Information")
        print("3. Exit")
        choice2 = input("Select an option (1/2/3): ")

        
        if choice2 == "1":
            print_separator("New Patient")
            patientName = input("\nPatient Name: ")

            speedMap = {'a': 1, 'b': 2, 'c': 3, 'd': 5}

            print("Patient walking speed: ")
            print("a. Wheelchair    b. Cane     c. Walk   d. Run")
            speedInput = input("Enter Speed: ")
            
            print_separator("Curfew Instrucitons")
            print("Please enter the time as the hour on a 24 hour clock: ex. 18 = 6pm")

            print("\nPatient Curfew Time: ")
            curfewInput = input("Enter Curfew on 24 hour clock: ")
            patientCurfew = int(curfewInput)

            print("\nPatient Wake Time: ")
            wakeInput = input("Enter Time on 24 hour clock: ")
            patientWake = int(wakeInput)


            if speedInput in speedMap and patientCurfew < 25 and patientWake < 12:
                patientSpeed = speedMap[speedInput]

                patientInfo.append(patientName)
                patientInfo.append(patientSpeed)
                patientInfo.append(patientCurfew)
                patientInfo.append(patientWake)
            
            
            else:
                print("Invalid input. Please enter 'a', 'b', 'c', or 'd'")

            print(patientInfo)
    
        elif choice2 == "2":
            print_separator("Patient Information")
            print(patientInfo)
            
    else:
        print("Incorrect login")
    
    
elif choice == '2':
    print("Exiting the program.")

else:
    print("Invalid choice. Please enter 1 or 2.")

ble = bluetooth.BLE()
p = BLESimplePeripheral(ble)    
    
print("Please use LightBlue to connect to ESP32.")

time.sleep_ms(2000)
sentryMode = True
personPasses = False
onTheLoose = False

startTimeOnLoose = time.time()

def on_rx(rx_data):
    global sentryMode
    global onTheLoose
    print("Received: ", rx_data)
    if rx_data == b'found':
        print("found")
        sentryMode = True
        onTheLoose = False
        displayMain()
    else:
        pass
    
displayMain()
while True:
    if sentryMode:
        time.sleep_ms(500)
        distanceMeasured = getSonar()
        print('Distance: ',distanceMeasured,'cm' )
        if distanceMeasured < distanceThreshold:
            sentryMode = False
            personPasses = True
    
    if personPasses:
        passDisplay()
        print("please enter your password:")
        # Run Romain's keypad code
        startTime = time.time()

        while True:
            keydata = key()
            if keydata is not None:
                keyIn[keyInNum] = keydata
                keyInNum += 1

            if keyInNum == 4:
                if keyIn == keyOut:
                    print("Password right!")
                    # Reset pass key in
                    keyIn = ['', '', '', '']
                    sentryMode = True
                    personPasses = False
                    keyInNum = 0
                    tries = 0
                    time.sleep(10)
                    displayMain()
                    break
                else:
                    print("Password error!")
                    # Have retry logic, send a message via Bluetooth
                    tries += 1
                    # Reset pass key in
                    keyIn = ['', '', '', '']
                    # Restart timer for the homeowner if they get it wrong
                    startTime = time.time()

                    if tries >= 3:
                        print("someone is trying to escape")

                keyInNum = 0

            currentTime = time.time()

            # Checking not too much time has been spent since sonar was triggered
            if (currentTime - startTime) >= 15:
                # Notify homeowner that someone is on the loose
                personPasses = False
                onTheLoose = True
                startTimeOnLoose = time.time()
                messageOut = "person on the loose"
                print(messageOut)
                p.send(messageOut)
                time.sleep(5)
                break
        
    if onTheLoose:
   
        currentTimeOnLoose = time.time()
        distanceLoose = str(patientInfo[1] * (currentTimeOnLoose - startTimeOnLoose))
        timeLoose = str(currentTimeOnLoose - startTimeOnLoose)
        messageOut = ("Patient has left " + timeLoose + " secs ago")
        print(messageOut)
        p.send(messageOut)
            
        messageOut = ("Patient could be " + distanceLoose + " meters away")
        print(messageOut)
        p.send(messageOut)
        timeDisplay(int(timeLoose), distanceLoose)
        time.sleep(10)
        p.on_write(on_rx)
        
        
        