from nokkhum import models
import datetime

import asyncio
import logging
import pathlib
import tarfile
import os
import concurrent.futures

logger = logging.getLogger(__name__)


class StorageController:
    def __init__(self, settings):
        self.settings = settings
        self.path = pathlib.Path(self.settings["NOKKHUM_PROCESSOR_RECORDER_PATH"])
        self.pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=settings.get("NOKKHUM_CONTROLLER_COMPRESSION_MAX_WORKER")
        )
        self.compression_queue = asyncio.queues.Queue(maxsize=100)

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

    def compress(self, output_filename, video):
        with tarfile.open(output_filename, f"w:{self.settings['TAR_TYPE']}") as tar:
            tar.add(video, arcname=os.path.basename(video))
            return video

    async def process_compression_result(self):
        if self.image_queue.empty():
            # await asyncio.sleep(0.1)
            return

        while not self.compression_queue.empty():
            future_result = await self.compression_queue.get()
            while not future_result.done():
                await asyncio.sleep(0.001)
            video = future_result.result()
            # remove video

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
                    result = self.loop.run_in_executor(
                            self.pool, self.compress, output_filename, video
                        )
                    if not self.compression_queue.full():
                        self.compression_queue.put(result)
                    else:
                        return
                    