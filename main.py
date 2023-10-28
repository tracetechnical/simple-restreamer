import http.server
import logging
import os
import subprocess
import threading
import time
from multiprocessing import freeze_support
from socketserver import ThreadingMixIn

import cv2
import numpy as np


class CamHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.path)
        if self.path.endswith('.mjpg'):
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            while True:
                if self.server.started:
                    img = self.server.frame
                else:
                    img = np.zeros((1, 1, 3), dtype=np.uint8)

                r, buf = cv2.imencode(".jpg", img)
                if not r:
                    exit(-2)

                self.wfile.write("--jpgboundary\r\n".encode())
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', str(len(buf)))
                self.end_headers()
                self.wfile.write(bytearray(buf))
                self.wfile.write('\r\n'.encode())
                time.sleep(0.1)

        if self.path.endswith('.jpg'):
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.end_headers()
            if self.server.started:
                img = self.server.frame
            else:
                img = np.zeros((1, 1, 3), dtype=np.uint8)

            r, buf = cv2.imencode(".jpg", img)
            if not r:
                exit(-2)

            self.wfile.write(bytearray(buf))
            self.wfile.write('\r\n'.encode())

        if self.path.endswith('.html') or self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write('<html><head></head><body>')
            self.wfile.write(
                '<img src="cam.mjpg"/>')
            self.wfile.write('</body></html>')
            return


class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""


def open_cam_rtsp(uri, width, height, latency):
    """Open an RTSP URI (IP CAM)."""
    gst_str = (
        'rtspsrc location={} latency={} drop-on-latency=true ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! appsinkv max-buffers=1 drop=True').format(
        uri, latency)
    return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)


def thread_function(rtsp_url, server):
    logging.info("Cam Loading...")
    cap = open_cam_rtsp(rtsp_url, 1024, 768, 100)
    cap.setExceptionMode(True)
    logging.info("Cam Loaded...")
    while True:
        server.started = True
        if not cap.isOpened():
            logging.info("HUFFFFFFFFERS!")
        try:
            ret, server.frame = cap.read()
            if not ret:
                exit(-1)
        except Exception as inst:
            logging.info(type(inst))  # the exception type
            logging.info(inst.args)  # arguments stored in .args
            logging.info(inst)  # __str__ allows args to be printed directly,
            # but may be overridden in exception subclasses
            logging.info("EEEE")
            cap.release()
            cap = open_cam_rtsp(rtsp_url, 1024, 768, 100)


if __name__ == '__main__':
    logging.info(cv2.getBuildInformation())
    time.sleep(30)
    freeze_support()

    port = int(os.getenv("PORT"))
    if not port:
        port = 8000

    server = ThreadedHTTPServer(('', port), CamHandler)
    server.frame = np.zeros((1, 1, 3), dtype=np.uint8)
    server.started = False
    time.sleep(5)
    rtsp_path = os.getenv("RTSP_URL")
    if not rtsp_path:
        print("RTSP_URL environment varaible not defined")
        exit(-1)

    mjpeg = threading.Thread(target=thread_function, args=(rtsp_path, server), daemon=True)
    mjpeg.start()

    print("server started on: ")
    server.serve_forever()
