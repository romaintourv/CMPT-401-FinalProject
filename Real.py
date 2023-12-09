import bluetooth
import struct
import time
from ble_advertising import advertising_payload
from machine import Pin
from micropython import const
import utime
from keypad import KeyPad

keyPad = KeyPad(14, 27, 26, 25, 13, 21, 22, 23)

# Bluetooth constants
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

# Sonar constants
trigPin = Pin(33, Pin.OUT, 0)
echoPin = Pin(2, Pin.IN, 0)
soundVelocity = 340
distance_threshold = 50
activeBuzzer = Pin(12, Pin.OUT)

# States
onTheLoose = False
PersonPasses = False
sentryMode = True

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


def get_sonar_distance():
    trigPin.value(1)
    time.sleep_us(10)
    trigPin.value(0)
    while not echoPin.value():
        pass
    pingStart = time.ticks_us()
    while echoPin.value():
        pass
    pingStop = time.ticks_us()
    pingTime = time.ticks_diff(pingStop, pingStart)
    distance = pingTime * soundVelocity // 2 // 10000
    return int(distance)

def key():
    '''returns key value'''
    keyvalue = keyPad.scan()
    if keyvalue is not None:
        print('Your input:', keyvalue)
        time.sleep_ms(200)
        return keyvalue

def main():
    ble = bluetooth.BLE()
    p = BLESimplePeripheral(ble)

    def on_rx(rx_data):
        print("RX", rx_data)

    p.on_write(on_rx)

    print("Please use LightBlue to connect to ESP32.")
    
    # for key pad tries and inputs
    keyInNum = 0
    tries = 0

    # code that Josiah will provide
    keyOut = ['1', '2', '3', '4']

    # key received
    keyIn = ['', '', '', '']

    patientCurfew = 18

    # Get the current time
    currentTime = utime.localtime()

    # Get only the hour
    currentHour = currentTime[3]

    print("Current Time:", "{:02d}".format(currentHour))

    # boolean to see if someone has escaped
    onTheLoose = False
    personPasses = True

    # Oke boolean detect person code:
    if personPasses:
        # If detects:
        # Run Romain's keypad code
        startTime = time.time()

        while True:
            keydata = key()
            if keydata is not None:
                keyIn[keyInNum] = keydata
                keyInNum += 1

            # Continuously monitor sonar
            current_distance = get_sonar_distance()
            print('Distance:', current_distance, 'cm')

            if current_distance < distance_threshold:
                # Someone is detected within the specified distance
                activeBuzzer.value(1)
                tx_data = "Someone is detected within the specified distance!"
                print("Send: ", tx_data)
                p.send(tx_data)
            else:
                # No one is detected or is beyond the threshold distance
                activeBuzzer.value(0)

            if keyInNum == 4:
                if keyIn == keyOut:
                    print("Password right!")
                    # Wait a couple of seconds then start checking for a person passing by
                    # Reset pass key in
                    keyIn = ['', '', '', '']
                    sentryMode = True
                    PersonPasses = False
                    time.sleep(2)  # Add a delay before the next sensor reading
                else:
                    print("Password error!")
                    # Have retry logic, send a message via Bluetooth
                    tries += 1
                    # Reset pass key in
                    keyIn = ['', '', '', '']
                    # Restart timer for the homeowner if they get it wrong
                    startTime = time.time()

                    if tries >= 3:
                        onTheLoose = True
                        print("Someone is trying to leave the house")
                        # Notify the homeowner but don't stop tries

                keyInNum = 0

            currentTime = time.time()

            # Checking not too much time has been spent since sonar was triggered
            if (currentTime - startTime) >= 15 and keydata is None:
                # Notify homeowner that someone is on the loose
                onTheLoose = True
                
            time.sleep(1)  # Add a delay before the next iteration

        if onTheLoose:
            tx_data2 = "Patient is on the loose"
            print("Send: ", tx_data2)
            p.send(tx_data2)
            startTimer = time.time()

if __name__ == "__main__":
    main()