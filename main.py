import http.server
import logging
import os
import threading
import cv2
import numpy as np
import queue
from multiprocessing import freeze_support
from socketserver import ThreadingMixIn


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

class VideoCapture:

  def __init__(self, name):
    self.name = name
    self.cap = cv2.VideoCapture(name, cv2.CAP_GSTREAMER)
    self.q = queue.Queue()
    t = threading.Thread(target=self._reader)
    t.daemon = True
    t.start()

  # read frames as soon as they are available, keeping only most recent one
  def _reader(self):
    while True:
        if not self.cap.isOpened():
            logging.info("HUFFFFFFFFERS!")
        try:
            ret, frame = self.cap.read()
            if not ret:
                self.cap = cv2.VideoCapture(self.name, cv2.CAP_GSTREAMER)
            else:
                if not self.q.empty():
                    try:
                      self.q.get_nowait()   # discard previous (unprocessed) frame
                    except queue.Empty:
                      pass
                self.q.put(frame)
        except Exception as e:
            logging.error(e)
            pass

  def read(self):
    return self.q.get()

class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""

def thread_function(rtsp_url, server):
    logging.info("Cam Loading...")
    cap = VideoCapture(rtsp_url)
    logging.info("Cam Loaded...")
    while True:
        server.started = True
        try:
            frame = cap.read()
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            r2, frameOutr = cv2.imencode(".jpg", frame, encode_param)
            server.frameOut = frameOutr
        except Exception as inst:
            logging.info(type(inst))  # the exception type
            logging.info(inst.args)  # arguments stored in .args
            logging.info(inst)  # __str__ allows args to be printed directly,
            # but may be overridden in exception subclasses
            logging.info("Exception: ----0-0-0-0----")

def reconn(cap, rtsp_url):
    cap.release()
    return cv2.VideoCapture(rtsp_url, cv2.CAP_GSTREAMER)


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
