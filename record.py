import time
import signal
import cv2
import threading
import argparse
from datetime import datetime
from imx519.JetsonCamera import Camera
from imx519.Focuser import Focuser
from imx519.Autofocus import FocusState, doFocus

exit_ = False
recording = False
video_writer = None

def sigint_handler(signum, frame):
    global exit_
    exit_ = True

signal.signal(signal.SIGINT, sigint_handler)
signal.signal(signal.SIGTERM, sigint_handler)

def parse_cmdline():
    parser = argparse.ArgumentParser(description='Arducam IMX519 Autofocus Demo.')

    parser.add_argument('-i', '--i2c-bus', type=int, nargs=None, required=True,
                        help='Set i2c bus, for A02 is 6, for B01 is 7 or 8, for Jetson Xavier NX it is 9 and 10.')

    parser.add_argument('-v', '--verbose', action="store_true", help='Print debug info.')

    return parser.parse_args()

def start_recording(frame):
    global video_writer
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    now = datetime.now()
    file_name = now.strftime("output_%m_%d_%H_%M.avi")
    video_writer = cv2.VideoWriter(file_name, fourcc, 30.0, (frame.shape[1], frame.shape[0]))

def stop_recording():
    global video_writer
    if video_writer:
        video_writer.release()
        video_writer = None
        print("Recording stopped and saved to output.avi")

if __name__ == "__main__":
    args = parse_cmdline()
    camera = Camera()
    focuser = Focuser(args.i2c_bus)
    focuser.verbose = args.verbose

    focusState = FocusState()
    focusState.verbose = args.verbose
    doFocus(camera, focuser, focusState)

    start = time.time()
    frame_count = 0

    while not exit_:
        frame = camera.getFrame(2000)

        cv2.imshow("Test", frame)

        key = cv2.waitKey(1)
        
        if key == ord('q'):  # Press 'q' to quit
            exit_ = True
        elif key == ord('f'):  # Press 'f' to reset and refocus
            if focusState.isFinish():
                focusState.reset()
                doFocus(camera, focuser, focusState)
            else:
                print("Focus is not done yet.")
        elif key == ord('r'):  # Press 'r' to start/stop recording
            if recording:
                stop_recording()
                recording = False
            else:
                start_recording(frame)
                recording = True
                print("Recording started.")
        
        # Write the frame to the video file if recording
        if recording and video_writer:
            video_writer.write(frame)

        frame_count += 1
        if time.time() - start >= 1:
            print("{}fps".format(frame_count))
            start = time.time()
            frame_count = 0

    # Clean up and release resources when exiting
    if video_writer:
        stop_recording()

    camera.close()
    cv2.destroyAllWindows()

