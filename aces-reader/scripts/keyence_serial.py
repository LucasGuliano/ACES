import time
import serial

_serial = serial.Serial(
    # This port will likely differ on a different computer/USB adapter
    port='/dev/tty.usbserial-21340',
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)

_serial.isOpen()
# Put the Keyence in "General Mode"
# _serial.write("R0\r".encode())
# p. 5-21 in the manual: synchronization setting
# _serial.write("SW,OJ,01,0\r".encode())
# print('Enter your commands below.\r\nInsert "exit" to leave the application.')

while 1:
    # get keyboard input
    # Python 3 users
    # _input = input(">> ") + '\r'

    _input = "MS,01\r"
    if input == 'exit':
        _serial.close()
        exit()
    else:
        # send the character to the device
        print("Asking for data")
        _serial.write(_input.encode())
        # Give device time to respond
        # 1/500 appears to be fastest before the serial line starts missing data.
        time.sleep(1)
        out = b''
        while _serial.inWaiting() > 0:
            out += _serial.read(1)

        if out != b'':
            print(out)
