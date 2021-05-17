from nokkhum import models
import datetime

# import asyncio
import logging
import pathlib
import tarfile
import os
logger = logging.getLogger(__name__)


class StorageController:
    def __init__(self, settings):
        self.settings = settings
        self.path = pathlib.Path(self.settings["NOKKHUM_PROCESSOR_RECORDER_PATH"])

    async def remove_expired_video_records(self):
        logger.debug("start remove expired records")

        processors = models.Processor.objects()
        for processor in processors:

            storage_period = processor.storage_period
            if storage_period == 0:
                continue
            expired_date = datetime.date.today() - datetime.timedelta(
                days=storage_period
            )
            # logger.debug(f'{expired_date}')
            expired_date = datetime.datetime.combine(
                expired_date, datetime.time(0, 0, 0)
            )

            files_path = self.path / str(processor.id)
            if not files_path.exists() and not files_path.is_dir():
                continue

            logger.debug(f"start remove file {files_path}")
            for dir_file in files_path.iterdir():
                if not dir_file.name.isdigit():
                    continue

                year = int(dir_file.name[0:4])
                month = int(dir_file.name[4:6])
                day = int(dir_file.name[6:8])
                # logger.debug(f'{dir_file.name}')

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

    async def compress_video_files(self):
        logger.debug("start compress file mkv")
        for processor_dir in self.path.iterdir():
            for date_dir in processor_dir.iterdir():
                if not (date_dir.name).isdigit():
                    continue
                for video in date_dir.iterdir():
                    if video.name.split(".")[1] != "mkv":
                        continue
                    if video.name[0] == "_":
                        continue
                    logger.debug(video)
                    output_filename = f'{date_dir/pathlib.Path(video.name.split(".")[0])}.tar.{self.settings["TAR_TYPE"]}'
                    with tarfile.open(output_filename, f"w:{self.settings['TAR_TYPE']}") as tar:
                        tar.add(video, arcname=os.path.basename(video))
                    