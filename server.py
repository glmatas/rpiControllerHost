import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

lights = {'yellow_light': 14, 'green_light': 27, 'red_light': 4}  # GPIO pins for lights

for pin in lights.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)  # Ensure all lights start off

try:
    while True:
        for color, pin in lights.items():
            print(f"Turning on {color}")
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(1)  # Leave the light on for 1 second
            print(f"Turning off {color}")
            GPIO.output(pin, GPIO.LOW)
            time.sleep(1)  # Leave the light off for 1 second
except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()
