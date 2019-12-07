from nokkhum import models
from mongoengine.queryset.visitor import Q
import datetime
# import asyncio
import logging
import pathlib

logger = logging.getLogger(__name__)


class ResultController:
    def __init__(self, settings):
        self.settings = settings
        self.path = pathlib.Path(self.settings['NOKKHUM_PROCESSOR_RECORDER_PATH'])

    def expired_video_records(self):
        logger.debug('start remove expired records')

        processors = models.Processor.objects()
        for processor in processors:

            storage_period = int(processor.storage_period)
            if storage_period == 0:
                continue
            expired_date = datetime.date.today() - datetime.timedelta(days=storage_period)
            # logger.debug(f'{expired_date}')
            expired_date = datetime.datetime.combine(expired_date,
                                                     datetime.time(0, 0, 0))

            files_path = self.path / str(processor.id)
            if not files_path.exists() and not files_path.is_dir():
                return
            logger.debug(f'start remove file {file_path}')
            for dir_file in files_path.iterdir():
                year = int(dir_file.name[0:4])
                month = int(dir_file.name[4:6])
                day = int(dir_file.name[6:8])
                # logger.debug(f'{dir_file.name}')

                logger.debug(f'{datetime.datetime(year, month, day)}')

                logger.debug(f'{expired_date}')
                if datetime.datetime(year, month, day) > expired_date:
                    # logger.debug('not expired')
                    continue

                # logger.debug('expired')
                images_path = files_path / dir_file
                # logger.debug(f'{images_path}')
                for image_file in images_path.iterdir():
                    # logger.debug(f'>>>>> {image_file}')
                    image_file.unlink()

                dir_file.rmdir()
