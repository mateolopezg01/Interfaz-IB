import serial
import time

# Replace 'COM3' with the appropriate port for your Arduino
# On Linux/Mac, it might be something like '/dev/ttyACM0' or '/dev/ttyUSB0'
arduino_port ='/dev/cu.usbmodem1101'
baud_rate = 2000000

# Establish a serial connection to the Arduino
ser = serial.Serial(arduino_port, baud_rate)
time.sleep(2)  # Wait for the connection to be established

def led_on():
    ser.write(b'1')  # Send the '1' command to turn the LED on

def led_off():
    ser.write(b'0')  # Send the '0' command to turn the LED off

try:
    while True:
        command = input("Enter 'on' to turn on the LED, 'off' to turn off the LED, or 'quit' to exit: ").strip().lower()
        if command == 'on':
            led_on()
        elif command == 'off':
            led_off()
        elif command == 'quit':
            break
        else:
            print("Invalid command. Please enter 'on', 'off', or 'quit'.")
finally:
    ser.close()  # Close the serial connection
