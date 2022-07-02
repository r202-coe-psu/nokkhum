import threading
import datetime
import time

import cv2

import logging

logger = logging.getLogger(__name__)


class OpenCVMotionDetector:
    def __init__(self, frame=None, sensitivity=0.998):
        self.sensitivity = sensitivity
        self.default_threshold_value = sensitivity

        self.avg_frame = None
        if frame:
            self.initial(frame)

        self.processing_size = (800, 600)

    def initial(self, frame):
        frame = self.resize_image(frame)
        height, width, _ = frame.shape
        self.default_threshold_value = width * height * (1 - self.sensitivity)
        blur = self.get_gray_and_blur(frame)
        self.update_pattern_frame(blur)

    def resize_image(self, frame):

        processing_size = self.processing_size
        height, width, _ = frame.shape
        if width > self.processing_size[0]:
            factor = width / self.processing_size[0]
            processing_size = (int(width / factor), int(height / factor))

        img = frame
        if width > processing_size[0] or height > processing_size[1]:
            img = cv2.resize(frame, processing_size, interpolation=cv2.INTER_AREA)

        return img

    def get_gray_and_blur(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (21, 21), 0)
        return blur

    def update_pattern_frame(self, frame):
        # self.avg_frame = self.get_gray_and_blur(frame).astype("float")

        self.avg_frame = frame.astype("float")
        self.frame_scale_abs = cv2.convertScaleAbs(self.avg_frame)

    def has_motion(self, frame):
        if self.avg_frame is None:
            self.initial(frame)
            return False

        frame = self.resize_image(frame)

        blur = self.get_gray_and_blur(frame)
        cv2.accumulateWeighted(blur, self.avg_frame, 0.5)
        frame_delta = cv2.absdiff(blur, self.frame_scale_abs)
        thresh = cv2.threshold(frame_delta, 5, 255, cv2.THRESH_BINARY)[1]

        count_non_zero = cv2.countNonZero(thresh)

        # if count_non_zero > self.default_threshold_value/2:
        #     self.update_pattern_frame(blur)
        #     logger.debug(f'update motion {count_non_zero}/{self.default_threshold_value} -> {frame.shape}')

        self.update_pattern_frame(blur)

        if count_non_zero < self.default_threshold_value:
            return False

        # cv2.imshow('motion', frame)
        logger.debug(
            f"has motion {count_non_zero}/{self.default_threshold_value} -> {frame.shape}"
        )
        return True


class MotionDetector(threading.Thread):
    def __init__(
        self,
        input_queue,
        output_queues=[],
        duration=3,
        wait_motion_time=1,
    ):
        super().__init__()
        self.name = "Motion Dectector"
        self.running = False
        self.input_queue = input_queue
        self.output_queues = output_queues
        self.daemon = True

        self.detector = OpenCVMotionDetector()
        self.tmp_queue = []
        self.duration = duration
        self.wait_motion_time = wait_motion_time

    def stop(self):
        self.running = False

    def put_output_queues(self):
        for img in self.tmp_queue:
            for q in self.output_queues:
                q.put(img)

        self.tmp_queue.clear()

    def run(self):
        self.running = True
        logger.debug("Start Motion Detector")

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

            # cv2.imshow("img", image.data)
            # cv2.waitKey(10)

            current_date = datetime.datetime.now()
            if not self.detector.has_motion(image.data):
                # print('last motion', (current_date - last_motion_date).seconds)

                # no motion but last motion less than wait_motion_time
                if (current_date - last_motion_date).seconds < self.wait_motion_time:
                    self.put_output_queues()
                    continue

                # remove image from queue when no motion and last motion more than wait_motion_time
                for img in self.tmp_queue[:]:
                    if (
                        current_date - img.captured_date
                    ).seconds > self.wait_motion_time:
                        self.tmp_queue.remove(img)
                        # logger.debug(f'nomotion, drop image')
                    else:
                        break

                continue

            last_motion_date = datetime.datetime.now()
            self.put_output_queues()

        logger.debug("End Motion Detector")
