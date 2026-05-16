import socketio
import subprocess
import json
import time

SERVER = "http://172.20.10.8:5050"

sio = socketio.Client()

@sio.event
def connect():
    print("Connected to server")

@sio.event
def disconnect():
    print("Disconnected")

sio.connect(SERVER)

while True:
    try:
        result = subprocess.check_output(
            ["termux-location", "-p", "network"]
        )

        loc = json.loads(result)
        data = {
            "lat": loc["latitude"],
            "lon": loc["longitude"]
        }
        print("Sent:", data)

        sio.emit("location", data)

    except Exception as e:
        print("Error:", e)