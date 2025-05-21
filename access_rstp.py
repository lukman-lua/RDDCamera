import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

Gst.init(None)

pipeline_str = (
    "v4l2src device=/dev/video0 ! "
    "video/x-raw,width=1920,height=1080,framerate=30/1 ! "
    "videoconvert ! "
    "autovideosink"
)

pipeline = Gst.parse_launch(pipeline_str)
pipeline.set_state(Gst.State.PLAYING)

loop = GObject.MainLoop()
try:
    loop.run()
except KeyboardInterrupt:
    pipeline.set_state(Gst.State.NULL)

