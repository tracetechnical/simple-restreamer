import os
import cv2
import json
import queue
import logging
import threading
import datetime
import numpy as np

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from multiprocessing import freeze_support


# =============================
# Configuration
# =============================

MJPEG_BOUNDARY = "--jpgboundary"
JPEG_QUALITY = 80
FONT = cv2.FONT_HERSHEY_SIMPLEX


# =============================
# HTTP Handler
# =============================

class CamHandler(BaseHTTPRequestHandler):
    """Serves MJPEG streams, JPEG snapshots, and a simple index page."""

    def log_request(self, code='-', size='-'):
        # Silence default HTTP logging
        pass

    def do_GET(self):
        try:
            if self.path.endswith(".mjpg"):
                self._serve_mjpeg()
            elif self.path.endswith(".jpg"):
                self._serve_jpeg()
            elif self.path == "/" or self.path.endswith(".html"):
                self._serve_index()
        except BrokenPipeError:
            # Client disconnected
            pass

    # ---------- Helpers ----------

    def _get_requested_frame(self) -> bytes:
        """Return full frame or named section frame if requested."""
        if "/section/" not in self.path:
            return server.frame_out

        section_name = self.path.split("/section/")[1].split("/")[0]
        return server.slices.get(section_name, server.frame_out)

    # ---------- Endpoints ----------

    def _serve_mjpeg(self):
        self.send_response(200)
        self.send_header(
            "Content-Type",
            f"multipart/x-mixed-replace; boundary={MJPEG_BOUNDARY}"
        )
        self.end_headers()

        while True:
            frame = self._get_requested_frame()

            self.wfile.write(f"{MJPEG_BOUNDARY}\r\n".encode())
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(frame)))
            self.end_headers()
            self.wfile.write(frame)
            self.wfile.write(b"\r\n")

    def _serve_jpeg(self):
        frame = self._get_requested_frame()

        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(frame)))
        self.end_headers()
        self.wfile.write(frame)

    def _serve_index(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        body = {
            "available_sections": list(server.slices.keys())
        }

        self.wfile.write(b"<html><body>")
        self.wfile.write(json.dumps(body, indent=2).encode())
        self.wfile.write(b"</body></html>")


# =============================
# Video Capture
# =============================

class VideoCapture:
    """Threaded RTSP reader keeping only the most recent frame."""

    def __init__(self, rtsp_url: str):
        self.rtsp_url = rtsp_url
        self.queue = queue.Queue(maxsize=1)

        self.gst_pipeline = (
            f"rtspsrc location={rtsp_url} latency=100 drop-on-latency=true ! "
            "queue ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! "
            "appsink max-buffers=1 drop=true"
        )

        logging.info("GStreamer pipeline: %s", self.gst_pipeline)
        self.cap = cv2.VideoCapture(self.gst_pipeline, cv2.CAP_GSTREAMER)

        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        while True:
            if not self.cap.isOpened():
                logging.warning("Reopening RTSP stream")
                self.cap = cv2.VideoCapture(
                    self.gst_pipeline, cv2.CAP_GSTREAMER
                )

            ok, frame = self.cap.read()
            if not ok:
                continue

            if self.queue.full():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    pass

            self.queue.put(frame)

    def read(self) -> np.ndarray:
        return self.queue.get()


# =============================
# Frame Processing Thread
# =============================

def stream_worker(rtsp_url: str, server, extra_images):
    cap = VideoCapture(rtsp_url)
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]

    while True:
        frame = cap.read()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ---- Process slices ----
        for spec in extra_images:
            try:
                crop = frame[
                    spec["y_start"]:spec["y_end"],
                    spec["x_start"]:spec["x_end"]
                ].copy()

                cv2.putText(
                    crop, timestamp,
                    (10, 25),
                    FONT, 0.7,
                    (255,), 2
                )

                _, jpg = cv2.imencode(".jpg", crop, encode_params)
                server.slices[spec["name"]] = jpg.tobytes()

            except Exception:
                logging.exception("Slice processing failed")

        # ---- Full frame ----
        _, full_jpg = cv2.imencode(".jpg", frame, encode_params)
        server.frame_out = full_jpg.tobytes()


# =============================
# Main
# =============================

if __name__ == "__main__":
    freeze_support()
    logging.basicConfig(level=logging.INFO)

    port = int(os.getenv("PORT", "8000"))
    rtsp_url = os.getenv("RTSP_URL")
    extra_img = os.getenv("EXTRA_IMG")

    if not rtsp_url:
        raise RuntimeError("RTSP_URL environment variable is required")

    extra_images = json.loads(extra_img) if extra_img else []

    server = ThreadingHTTPServer(("", port), CamHandler)

    # Shared server state
    _, blank = cv2.imencode(".jpg", np.zeros((1, 1, 3), np.uint8))
    server.frame_out = blank.tobytes()
    server.slices = {}

    threading.Thread(
        target=stream_worker,
        args=(rtsp_url, server, extra_images),
        daemon=True
    ).start()

    logging.info("MJPEG server running on port %d", port)
    server.serve_forever()
