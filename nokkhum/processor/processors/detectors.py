import threading
import time

import cv2

import logging
logger = logging.getLogger(__name__)


class MotionDetector:
    def __init__(self, frame=None, threshold=100):
        self.default_threshold_value = threshold

        self.avg_frame = None
        if frame:
            self.avg_frame = self.get_gray_and_blur(frame).astype("float")


    def get_gray_and_blur(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (21, 21), 0)
        return blur


    def has_motion(self, frame):
        if self.avg_frame is None:
            self.avg_frame = self.get_gray_and_blur(frame).astype("float")
            return False

        blur = self.get_gray_and_blur(frame)
        cv2.accumulateWeighted(blur, self.avg_frame, 0.5)
        frame_delta = cv2.absdiff(blur, cv2.convertScaleAbs(self.avg_frame))
        thresh = cv2.threshold(frame_delta,
                               5,
                               255,
                               cv2.THRESH_BINARY)[1]

        if cv2.countNonZero(thresh) < self.default_threshold_value:
            return False
        
        return True




class MotionDetector(threading.Thread):
    def __init__(self,
                 uri,
                 input_queue,
                 output_queues=[]):
        super().__init__()
        self.uri = uri
        self.running = False
        self.queues = queues
        self.daemon = True

    def stop(self):
        self.running = False

    def run(self):
        self.running = True
        logger.debug('Start Motion Detector')

        while self.running:
            img = input_queue.get()
            if img is None:
                self.running = False
                break
            
            for q in self.queues:
                q.put(img)

        logger.debug('End Motion Detector')
