import http.server
import multiprocessing as mp
import socketserver
import threading
import time
import os
from multiprocessing import freeze_support
from socketserver import ThreadingMixIn
from typing import Tuple

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


def thread_function(rtsp_url, server):
    print("Cam Loading...")
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_GSTREAMER)
    cap.setExceptionMode(True)
    print("Cam Loaded...")
    while True:
        server.started = True
        if not cap.isOpened():
            print("HUFFFFFFFFERS!")
        try:
            ret, server.frame = cap.read()
            if not ret:
                exit(-1)
        except:
            print("EEEE")
            cap.release()
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)


if __name__ == '__main__':
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
