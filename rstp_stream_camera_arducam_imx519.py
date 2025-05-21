import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')

from gi.repository import Gst, GstRtspServer, GObject

# Inisialisasi GStreamer
Gst.init(None)

class RTSPServer:
    def __init__(self, device="/dev/video0"):
        self.server = GstRtspServer.RTSPServer()
        self.factory = GstRtspServer.RTSPMediaFactory()

        # Pipeline RTSP tanpa autofocus
        pipeline = (
            f"( v4l2src device={device} ! "
            "video/x-raw,width=1920,height=1080,framerate=30/1 ! "
            "videoconvert ! "
            "x264enc tune=zerolatency bitrate=2000 speed-preset=superfast ! "
            "rtph264pay name=pay0 pt=96 )"
        )

        self.factory.set_launch(pipeline)
        self.factory.set_shared(True)
        self.server.get_mount_points().add_factory("/stream", self.factory)
        self.server.attach(None)
        print("RTSP stream ready at rtsp://<your-ip>:8554/stream")

if __name__ == "__main__":
    server = RTSPServer("/dev/video0")
    loop = GObject.MainLoop()
    loop.run()

