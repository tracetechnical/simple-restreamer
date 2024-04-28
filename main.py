from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import logging
import os
import threading
import cv2
import numpy as np
import queue
import json
import datetime
from multiprocessing import freeze_support


class CamHandler(BaseHTTPRequestHandler):
    def log_request(self, code='-', size='-') -> None:
        pass

    def do_GET(self):
        if self.path.endswith('.mjpg'):
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            while True:
                self.wfile.write("--jpgboundary\r\n".encode())
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', str(len(server.frameOut)))
                self.end_headers()
                frame = server.frameOut
                if self.path.__contains__('/section/'):
                    section_fragment = self.path.split('/section/')[1]
                    section_name = section_fragment.split('/')[0]
                    print(section_fragment)
                    print(section_name)
                    section = server.slices[section_name]
                    if section:
                        print("Got sect")
                        frame = section
                self.wfile.write(frame)
                self.wfile.write('\r\n'.encode())

        if self.path.endswith('.jpg'):
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.end_headers()
            frame = server.frameOut
            if self.path.__contains__('/section/'):
                section_fragment = self.path.split('/section/')[1]
                section_name = section_fragment.split('/')[0]
                print(section_fragment)
                print(section_name)
                section = server.slices[section_name]
                if section:
                    print("Got sect")
                    frame = section
            self.wfile.write(frame)
            self.wfile.write('\r\n'.encode())

        if self.path.endswith('.html') or self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write('<html><head></head><body>')
            self.wfile.write('' + json.dumps(server.slices))
            self.wfile.write('</body></html>')
            return


class VideoCapture:

  def __init__(self, name):
    self.name = name
    self.gst = f"rtspsrc location={self.name} latency=0 drop-on-latency=true ! queue ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! appsink max-buffers=1 drop=True"
    logging.info(f"GST String is '{self.gst}'")
    self.cap = cv2.VideoCapture(self.gst, cv2.CAP_GSTREAMER)
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
                self.cap = cv2.VideoCapture(self.gst, cv2.CAP_GSTREAMER)
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


def thread_function(rtsp_url, server):
    logging.info("Cam Loading...")
    cap = VideoCapture(rtsp_url)
    logging.info("Cam Loaded...")
    extra_images = []
    if extra_img:
        extra_images = json.loads(extra_img)
    while True:
        server.started = True
        try:
            frame = cap.read()
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            try:
                print(extra_images)
                for extra in extra_images:
                    x_start = extra['x_start']
                    x_end = extra['x_end']
                    y_start = extra['y_start']
                    y_end = extra['y_end']
                    sliced_image = frame[y_start:y_end, x_start:x_end].copy()
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cv2.putText(sliced_image, timestamp, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,), 2)
                    cv2.putText(sliced_image, timestamp, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,), 1)
                    r3, sliceFrame = cv2.imencode(".jpg", sliced_image, encode_param)
                    server.slices[extra['name']] = sliceFrame.tobytes()
            except Exception as inst:
                logging.info(type(inst))  # the exception type
                logging.info(inst.args)  # arguments stored in .args
                logging.info(inst)  # __str__ allows args to be printed directly,
                # but may be overridden in exception subclasses
                logging.info("Exception: ----1-1-1-1----")
            r2, frameOutr = cv2.imencode(".jpg", frame, encode_param)
            server.frameOut = frameOutr.tobytes()
        except Exception as inst:
            logging.info(type(inst))  # the exception type
            logging.info(inst.args)  # arguments stored in .args
            logging.info(inst)  # __str__ allows args to be printed directly,
            # but may be overridden in exception subclasses
            logging.info("Exception: ----0-0-0-0----")


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.info(cv2.getBuildInformation())
    freeze_support()

    port = int(os.getenv("PORT"))

    extra_img = os.getenv("EXTRA_IMG")

    if not port:
        port = 8000

    server = ThreadingHTTPServer(('', port), CamHandler)
    server.started = False
    r, frameOut = cv2.imencode(".jpg", np.zeros((1, 1, 3), dtype=np.uint8))
    server.frameOut = frameOut.tobytes()
    server.slices = {}
    rtsp_path = os.getenv("RTSP_URL")
    if not rtsp_path:
        print("RTSP_URL environment variable not defined")
        exit(-1)

    mjpeg = threading.Thread(target=thread_function, args=(rtsp_path, server), daemon=True)
    mjpeg.start()

    print("server started")
    server.serve_forever()
