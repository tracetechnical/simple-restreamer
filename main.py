import http.server
import logging
import os
import threading
import time
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
                logging.info(str(len(server.frameOut)))
                self.send_header('Content-length', str(len(server.frameOut)))
                self.end_headers()
                self.wfile.write(bytearray(server.frameOut))
                self.wfile.write('\r\n'.encode())
                time.sleep(0.1)

        if self.path.endswith('.jpg'):
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.end_headers()

            self.wfile.write(bytearray(frameOut))
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


def open_cam_rtsp(uri, width, height, latency):
    """Open an RTSP URI (IP CAM)."""
    gst_str = (
        'rtspsrc location={} latency={} drop-on-latency=true ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! appsink').format(
        uri, latency)
    logging.info("gst:" + gst_str)
    time.sleep(5)
    return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)


def thread_function(rtsp_url, server):
    global lo
    logging.info("Cam Loading...")
    cap = open_cam_rtsp(rtsp_url, 1024, 768, 100)
    cap.setExceptionMode(True)
    logging.info("Cam Loaded...")
    while True:
        server.started = True
        if not cap.isOpened():
            logging.info("HUFFFFFFFFERS!")
        try:
            logging.info("Read")
            ret, frame = cap.read()
            if not ret:
                frame = np.zeros((1, 1, 3), dtype=np.uint8)
            logging.info(ret)
            r2, frameOut = cv2.imencode(".jpg", frame)
            server.frameOut = frameOut
            logging.info(r2)
        except Exception as inst:
            logging.info(type(inst))  # the exception type
            logging.info(inst.args)  # arguments stored in .args
            logging.info(inst)  # __str__ allows args to be printed directly,
            # but may be overridden in exception subclasses
            logging.info("EEEE")
            cap.release()
            cap = open_cam_rtsp(rtsp_url, 1024, 768, 100)


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
