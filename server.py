import RPi.GPIO as GPIO
import socket
import json
import threading
import time
import signal
import sys

# GPIO setup
GPIO.setmode(GPIO.BCM)
lights = {'green_light': 23, 'yellow_light': 18, 'red_light': 4}  # GPIO pins for lights
buttons = {'yellow_button': 17, 'green_button': 27, 'red_button': 22}  # GPIO pins for buttons

# Setup GPIO pins for lights and buttons
for pin in lights.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)  # Start with all lights off

for pin in buttons.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Pull-down resistors for buttons

# Function to handle a clean shutdown on Ctrl+C
def signal_handler(sig, frame):
    print('Shutting down gracefully...')
    for pin in lights.values():
        GPIO.output(pin, GPIO.LOW)  # Turn off all lights
    GPIO.cleanup()
    server_socket.close()
    sys.exit(0)

# Register the signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

# Light startup animation
def startup_animation():
    for _ in range(3):
        for color in lights:
            GPIO.output(lights[color], GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(lights[color], GPIO.LOW)
    for color in lights:
        GPIO.output(lights[color], GPIO.HIGH)
    time.sleep(0.5)
    for color in lights:
        GPIO.output(lights[color], GPIO.LOW)

# Run the startup animation
startup_animation()

# Server setup
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 65432))  # Listening on all interfaces on port 65432
server_socket.listen(5)

def handle_client(client_socket):
    try:
        while True:
            # Receive JSON data from Unity client
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            print(f"Received: {data}")
            light_states = json.loads(data)
            
            # Update lights based on received JSON
            for color, state in light_states.items():
                if color in lights:
                    GPIO.output(lights[color], GPIO.HIGH if state else GPIO.LOW)
                    print(f"Set {color} to {'HIGH' if state else 'LOW'}")
            
            # Monitor button presses and send feedback to Unity
            while True:
                for color, pin in buttons.items():
                    button_state = GPIO.input(pin)
                    print(f"Button {color} state: {'HIGH' if button_state == GPIO.HIGH else 'LOW'}")
                    if button_state == GPIO.HIGH:
                        response = json.dumps({color: 'pressed'})
                        client_socket.send(response.encode('utf-8'))
                        print(f"Button {color.replace('_', ' ')} pressed, sent to Unity")
                        while GPIO.input(pin) == GPIO.HIGH:
                            pass  # Wait until the button is released
    except ConnectionResetError:
        print("Client disconnected")
    finally:
        client_socket.close()

while True:
    client_socket, addr = server_socket.accept()
    print(f"Connection from {addr}")
    client_handler = threading.Thread(target=handle_client, args=(client_socket,))
    client_handler.start()
