import RPi.GPIO as GPIO
import time

# GPIO setup
GPIO.setmode(GPIO.BCM)
buttons = {'yellow_button': 17, 'green_button': 27, 'red_button': 22}  # GPIO pins for buttons

# Setup GPIO pins for buttons
for pin in buttons.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Pull-down resistors for buttons

try:
    print("Press buttons to test (Ctrl+C to exit)")
    while True:
        for color, pin in buttons.items():
            button_state = GPIO.input(pin)
            if button_state == GPIO.LOW:
                print(f"{color.replace('_', ' ')} pressed")
        time.sleep(0.1)  # Small delay to prevent high CPU usage
except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()
