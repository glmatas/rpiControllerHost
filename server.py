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
    server_socket.close()  # Ensure server_socket is defined
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
    # Start the button monitoring in a separate thread
    button_thread = threading.Thread(target=monitor_buttons, args=(client_socket,), daemon=True)
    button_thread.start()

    try:
        buffer = ""  # Buffer to handle partial messages
        while True:
            # Receive JSON data from Unity client
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            
            buffer += data
            # Process each complete JSON object in the buffer
            while True:
                try:
                    # Attempt to parse a full JSON object from the buffer
                    json_object, buffer = extract_json_object(buffer)
                    if json_object is None:
                        break
                    print(f"Received: {json_object}")
                    light_states = json.loads(json_object)
                    
                    # Directly handle light control commands
                    for color, state in light_states.items():
                        if color in lights:
                            GPIO.output(lights[color], GPIO.HIGH if state else GPIO.LOW)
                            print(f"Set {color} to {'HIGH' if state else 'LOW'}")
                except json.JSONDecodeError:
                    break  # Wait for more data to complete the JSON object

    except (ConnectionResetError, OSError):
        print("Client disconnected or socket error")
    finally:
        client_socket.close()

def extract_json_object(buffer):
    """Extracts a complete JSON object from the buffer if possible."""
    open_braces = 0
    start_index = 0

    for i, char in enumerate(buffer):
        if char == '{':
            if open_braces == 0:
                start_index = i
            open_braces += 1
        elif char == '}':
            open_braces -= 1
            if open_braces == 0:
                return buffer[start_index:i+1], buffer[i+1:]

    return None, buffer  # No complete JSON object found

def monitor_buttons(client_socket):
    last_state = {color: GPIO.LOW for color in buttons}  # Track last state of each button
    try:
        while True:
            for color, pin in buttons.items():
                button_state = GPIO.input(pin)
                if button_state != last_state[color]:  # Detect state change
                    last_state[color] = button_state
                    if button_state == GPIO.HIGH:
                        response = json.dumps({"type": "button_press", "button": color}) + '\n'
                        try:
                            client_socket.send(response.encode('utf-8'))
                            print(f"Button {color.replace('_', ' ')} pressed, sent to Unity")
                        except OSError:
                            print("Failed to send data, client might have disconnected")
                            return
            time.sleep(0.1)  # Small delay to prevent high CPU usage
    except (ConnectionResetError, OSError):
        print("Client disconnected")
    finally:
        client_socket.close()

while True:
    client_socket, addr = server_socket.accept()
    print(f"Connection from {addr}")
    client_handler = threading.Thread(target=handle_client, args=(client_socket,))
    client_handler.start()
