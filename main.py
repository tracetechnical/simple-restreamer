import http.server
import logging
import os
import threading
from multiprocessing import freeze_support, Lock
from socketserver import ThreadingMixIn

import cv2
import numpy as np

lo = Lock()


class CamHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.path)
        if self.path.endswith('.mjpg'):
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            while True:
                self.wfile.write("--jpgboundary\r\n".encode())
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', str(len(server.frameOut)))
                self.end_headers()
                self.wfile.write(bytearray(server.frameOut))
                self.wfile.write('\r\n'.encode())

        if self.path.endswith('.jpg'):
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.end_headers()

            self.wfile.write(bytearray(server.frameOut))
            self.wfile.write('\r\n'.encode())

        if self.path.endswith('.html') or self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write('<html><head></head><body>')
            self.wfile.write('<img src="cam.mjpg"/>')
            self.wfile.write('</body></html>')
            return


class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""


def open_cam_rtsp(uri, rotation, latency):
    """Open an RTSP URI (IP CAM)."""
    rotation_str = ''
    if rotation == 90:
        rotation_str = 'videoflip method=clockwise'
    if rotation == 180:
        rotation_str = 'videoflip method=rotate-180'
    if rotation == 270:
        rotation_str = 'videoflip method=counterclockwise'

    gst_str = (
            'rtspsrc location={} latency=10 buffer-mode=auto drop-on-latency=true ! rtph264depay ! '
            'queue leaky=downstream ! h264parse ! decodebin ! ' + rotation_str + ' ! '
            'video/x-raw,width=1024,height=768 ! videoconvert ! queue leaky=downstream ! appsink').format(
        uri, latency)
    logging.info("gst:" + gst_str)
    return cv2.VideoCapture(uri, cv2.CAP_GSTREAMER)


def thread_function(rtsp_url, server):
    global lo

    rot_angle = int(os.getenv("ROTATION"))
    logging.info("Cam Loading...")
    cap = open_cam_rtsp(rtsp_url, rot_angle, 100)
    cap.setExceptionMode(True)
    logging.info("Cam Loaded...")
    while True:
        server.started = True
        if not cap.isOpened():
            logging.info("HUFFFFFFFFERS!")
        try:
            ret, frame = cap.read()
            if not ret:
                frame = np.zeros((1, 1, 3), dtype=np.uint8)
            r2, frameOutr = cv2.imencode(".jpg", frame)
            server.frameOut = frameOutr
            if not ret:
                cap = reconn(cap, rtsp_url, rot_angle)
        except Exception as inst:
            logging.info(type(inst))  # the exception type
            logging.info(inst.args)  # arguments stored in .args
            logging.info(inst)  # __str__ allows args to be printed directly,
            # but may be overridden in exception subclasses
            logging.info("Exception: ----0-0-0-0----")
            cap = reconn(cap, rtsp_url, rot_angle)


def reconn(cap, rtsp_url, rot_angle):
    cap.release()
    return open_cam_rtsp(rtsp_url, rot_angle, 100)


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.info(cv2.getBuildInformation())
    # time.sleep(30)
    freeze_support()

    port = int(os.getenv("PORT"))
    if not port:
        port = 8000

    server = ThreadedHTTPServer(('', port), CamHandler)
    server.started = False
    r, frameOut = cv2.imencode(".jpg", np.zeros((1, 1, 3), dtype=np.uint8))
    server.frameOut = frameOut
    # time.sleep(5)
    rtsp_path = os.getenv("RTSP_URL")
    if not rtsp_path:
        print("RTSP_URL environment varaible not defined")
        exit(-1)

    mjpeg = threading.Thread(target=thread_function, args=(rtsp_path, server), daemon=True)
    mjpeg.start()

    print("server started on: ")
    server.serve_forever()
