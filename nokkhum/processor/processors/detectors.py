import threading
import datetime
import time

import cv2

import logging
logger = logging.getLogger(__name__)


class OpenCVMotionDetector:
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
                 input_queue,
                 output_queues=[]):
        super().__init__()
        self.name = "Motion Dectector"
        self.running = False
        self.input_queue = input_queue
        self.output_queues = output_queues
        self.daemon = True

        self.detector = OpenCVMotionDetector()
        self.tmp_queue = []
        self.duration = 3
        self.wait_motion_time = 1

    def stop(self):
        self.running = False


    def put_output_queues(self):
        for img in self.tmp_queue:
            for q in self.output_queues:
                q.put(img)

        self.tmp_queue.clear()


    def run(self):
        self.running = True
        logger.debug('Start Motion Detector')

        counter = self.duration
        last_motion_date = datetime.datetime.now()

        while self.running:
            image = self.input_queue.get()
            if image is None:
                self.running = False
                break

            self.tmp_queue.append(image)
            if counter > 0:
                counter -= 1
            else:
                counter = self.duration

            current_date = datetime.datetime.now()
            if not self.detector.has_motion(image.data):
                # print('last motion', (current_date - last_motion_date).seconds)
                
                # no motion but last motion less than wait_motion_time
                if (current_date - last_motion_date).seconds < self.wait_motion_time:
                    self.put_output_queues()
                    continue

                # remove image from queue when no motion and last motion more than wait_motion_time
                for img in self.tmp_queue[:]:
                    if (current_date - img.captured_date).seconds > self.wait_motion_time:
                        self.tmp_queue.remove(img)
                        logger.debug(f'drop image')
                    else:
                        break

                continue

            last_motion_date = datetime.datetime.now()
            self.put_output_queues()

        logger.debug('End Motion Detector')
