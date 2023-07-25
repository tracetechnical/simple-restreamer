import http.server
import multiprocessing as mp
import time
import os
from multiprocessing import freeze_support

import cv2

class Camera():

    def __init__(self, rtsp_url):
        # load pipe for data transmittion to the process
        print("Starting pipe")
        self.parent_conn, child_conn = mp.Pipe()
        # load process
        print("Starting process")
        self.p = mp.Process(target=self.update, args=(child_conn, rtsp_url))
        # start process
        print("Starting daemon")
        self.p.daemon = True
        self.p.start()

    def end(self):
        # send closure request to process

        self.parent_conn.send(2)

    def update(self, conn, rtsp_url):
        # load cam into seperate process

        print("Cam Loading...")
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_GSTREAMER)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
        print("Cam Loaded...")
        run = True

        while run:

            # grab frames from the buffer
            cap.grab()

            # recieve input data
            rec_dat = conn.recv()

            if rec_dat == 1:
                # if frame requested
                ret, frame = cap.read()
                conn.send(frame)

            elif rec_dat == 2:
                # if close requested
                cap.release()
                run = False

        print("Camera Connection Closed")
        conn.close()

    def get_frame(self, resize=None):
        ###used to grab frames from the cam connection process

        ##[resize] param : % of size reduction or increase i.e 0.65 for 35% reduction  or 1.5 for a 50% increase

        # send request
        self.parent_conn.send(1)
        frame = self.parent_conn.recv()

        # reset request
        self.parent_conn.send(0)

        # resize if needed
        if resize == None:
            return frame
        else:
            return self.rescale_frame(frame, resize)

    def rescale_frame(self, frame, percent=65):

        return cv2.resize(frame, None, fx=percent, fy=percent)


class CamHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.path)
        if self.path.endswith('.mjpg'):
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            while True:
                img = cam.get_frame()
                r, buf = cv2.imencode(".jpg", img)
                self.wfile.write("--jpgboundary\r\n".encode())
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', str(len(buf)))
                self.end_headers()
                self.wfile.write(bytearray(buf))
                self.wfile.write('\r\n'.encode())

        if self.path.endswith('.jpg'):
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            img = cam.get_frame()
            r, buf = cv2.imencode(".jpg", img)
            self.wfile.write("--jpgboundary\r\n".encode())
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-length', str(len(buf)))
            self.end_headers()
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


if __name__ == '__main__':
    freeze_support()
    print(cv2.getBuildInformation())
    port = 8000
    server = http.server.HTTPServer(('', port), CamHandler)
    time.sleep(5)
    rtsp_path = os.getenv("RTSP_URL")
    if not rtsp_path:
        print("RTSP_URL environment varaible not defined")
        exit(-1)
    path = "rtspsrc location=" + rtsp_path + " latency=0 ! rtph264depay ! h264parse !  appsink"
    print("Path is:" + path)
    cam = Camera(path)

    print(f"Camera is alive?: {cam.p.is_alive()}")

    print("server started on: ")
    server.serve_forever()
