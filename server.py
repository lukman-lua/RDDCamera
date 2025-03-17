from flask import Flask, Response
import cv2

app = Flask(__name__)

# Ganti ini dengan URL stream Anda
stream_url = "http://127.0.0.1:5000/video_feed"
camera = cv2.VideoCapture(stream_url)  # Menggunakan stream URL sebagai input


def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Encode frame ke format JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # Yield frame sebagai aliran MJPEG
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return '''
        <html>
            <head>
                <title>Video Streaming</title>
            </head>
            <body>
                <h1>Video Streaming</h1>
                <img src="/video" width="640" height="480">
            </body>
        </html>
    '''


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)  # Pastikan menggunakan port yang berbeda dari server utama
