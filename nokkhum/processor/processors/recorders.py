import time
import datetime
import threading
import pathlib
import cv2

import logging
logger = logging.getLogger(__name__)


class VideoRecorder(threading.Thread):
    def __init__(self,
                 queue,
                 processor_id='cam',
                 directory='/tmp',
                 extension='mp4',
                 api_preference=cv2.CAP_FFMPEG,
                 fps=15,
                 size=(640, 480),
                 minutes=10
                 ):
        super().__init__()
        self.running = False
        self.daemon=True
        self.directory = directory
        self.queue = queue
        self.writer = None
        self.processor_id = processor_id
        self.extension = extension
        self.encoder = self.get_encoder(extension)
        self.fps = fps
        self.size = size
        self.api_preference = api_preference
        if minutes > 2:
            self.duration = minutes * 60
        else:
            self.duration = 120

        self.filename = ''

    def get_encoder(self, extension):
        if extension == 'mp4':
            return cv2.VideoWriter_fourcc(*'X264') # small file high cpu
            # return cv2.VideoWriter_fourcc(*'mp4v') # big file low cpu
        elif extension == 'mkv':
            return cv2.VideoWriter_fourcc(*'X264')

        return cv2.VideoWriter_fourcc(*'MJPG')

    def get_new_recoder(self):
        now = datetime.datetime.now()

        path = pathlib.Path(self.directory) \
            / self.processor_id \
            / now.strftime('%Y%m%d')
        if not path.exists():
            path.mkdir(parents=True)

        filename = path / '_{}-{}.{}'.format(
                self.processor_id,
                now.strftime('%Y%m%d-%H%M%S-%f'),
                self.extension)

        if self.api_preference == cv2.CAP_GSTREAMER:
            filename = f'appsrc ! autovideoconvert ! x264enc ! mp4mux ! filesink location={filename}'
        writer = cv2.VideoWriter(str(filename),
                                 self.api_preference,
                                 self.encoder,
                                 self.fps,
                                 self.size,
                                 True)
        if not writer.isOpened():
            logger.debug(f'cannot open video writer encoder: {self.encoder} size: {self.size} fps: {self.fps}')
       
        self.filename = filename
        logger.debug(f'New video recorder {filename}')
        return writer

    def create_thumbnail(self, image):
        thumbnail_name = name = '{}/{}-thumbnail.png'.format(
                self.filename.parent,
                self.filename.stem[1:])
        cv2.imwrite(thumbnail_name, image)

    def stop(self):
        self.running = False

    def run(self):
        self.running = True
        writer = None
        image = self.queue.get()
        if image is None:
            self.running = False
        else:
            writer = self.get_new_recoder()
            self.create_thumbnail(image)

        begin_date = datetime.datetime.now()

        while self.running:
            try:
                image = self.queue.get()
                if image is None:
                    self.running = False
                    continue
            except Exception as e:
                logger.exeception(e)
                continue

            # cv2.imshow('test', image)
            # key = cv2.waitKey(10)
            # if key == ord('q'):
            #     break

            height, width, _ = image.shape
            if not width == self.size[0] or not height == self.size[1]:
                image = cv2.resize(image, self.size, interpolation = cv2.INTER_AREA)


            # check get new record
            current_date = datetime.datetime.now()
            if (current_date - begin_date).seconds >= self.duration:
                writer.release()
                self.filename.rename('{}/{}'.format(
                    self.filename.parent,
                    self.filename.name[1:]))

                writer = self.get_new_recoder()
                begin_date = current_date
                self.create_thumbnail(image)

            writer.write(image)

        if writer:
            writer.release()

            self.filename.rename('{}/{}'.format(
                self.filename.parent,
                self.filename.name[1:]))

        logger.debug('End recorder')
 
