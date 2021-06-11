from nokkhum import models
import datetime

import asyncio
import logging
import pathlib
import tarfile
import os
import concurrent.futures
import ffmpeg

logger = logging.getLogger(__name__)


class StorageController:
    def __init__(self, settings):
        self.settings = settings
        self.cache_path = pathlib.Path(
            self.settings["NOKKHUM_PROCESSOR_RECORDER_CACHE_PATH"]
        )
        self.recorder_path = pathlib.Path(
            self.settings["NOKKHUM_PROCESSOR_RECORDER_PATH"]
        )
        self.loop = asyncio.get_event_loop()
        self.compression_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=settings.get("NOKKHUM_COMPUTE_COMPRESSION_MAX_WORKER")
        )
        self.convertion_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=settings.get("NOKKHUM_COMPUTE_CONVERTION_MAX_WORKER")
        )
        self.compression_queue = asyncio.queues.Queue(maxsize=100)
        self.convertion_queue = asyncio.queues.Queue(maxsize=100)

    def compress(self, output_filename, video):
        with tarfile.open(output_filename, f"w:{self.settings['TAR_TYPE']}") as tar:
            tar.add(video, arcname=os.path.basename(video))
            return output_filename

    async def process_compression_result(self):
        if self.compression_queue.empty():
            return

        while not self.compression_queue.empty():
            future_result = await self.compression_queue.get()
            while not future_result.done():
                await asyncio.sleep(0.001)
            try:
                tar_file = future_result.result()
                logger.debug(tar_file)
                tar_path = pathlib.Path(tar_file)
                tar_path.rename(
                    pathlib.Path(
                        tar_file.replace("/_", "/").replace(
                            self.settings["NOKKHUM_PROCESSOR_RECORDER_CACHE_PATH"],
                            self.settings["NOKKHUM_PROCESSOR_RECORDER_PATH"],
                        )
                    )
                )
            except Exception as e:
                logger.exception(e)

    def check_video_file_name(self, video):
        filename = video.parents[0] / video.name[1:]
        if "motion" in video.name:
            _, date, time, _, _ = video.name.split("-")
        else:
            _, date, time, _ = video.name.split("-")
        file_date = datetime.datetime(
            int(date[:4]),
            int(date[4:6]),
            int(date[6:]),
            int(time[:2]),
            int(time[2:4]),
            int(time[4:]),
        )
        if (datetime.datetime.now() - file_date).seconds > 1200:
            video.rename(filename)
        return

    async def convert_video_files(self):
        logger.debug("start convert file mkv")
        data = {}
        try:
            for processor_dir in self.cache_path.iterdir():
                for date_dir in processor_dir.iterdir():
                    if not (date_dir.name).isdigit():
                        continue
                    for video in date_dir.iterdir():
                        if (date_dir / f"{video.name.split('.')[0]}.mp4").exists():
                            continue
                        if video.suffix != ".mkv":
                            continue
                        if video.name[0] == "_":
                            self.check_video_file_name(video)
                            continue
                        result = self.loop.run_in_executor(
                            self.convertion_pool, self.convert, video
                        )
                        if not self.convertion_queue.full():
                            await self.convertion_queue.put(result)
                        else:
                            return
        except Exception as e:
            logger.exception(e)

    def convert(self, video):
        try:
            logger.debug("converting")
            name = video.name.split(".")[0]
            with_mp4 = str(video.parents[0]) + "/_" + name + ".mp4"
            mp4_path = pathlib.Path(with_mp4.replace("/_", "/"))
            if mp4_path.exists():
                return
            result = (
                ffmpeg.input(video)
                .output(with_mp4)
                .run_async(overwrite_output=True, quiet=True)
            )
            logger.debug("waiting")
            result.wait()
            return result
        except Exception as e:
            logger.exception(e)

    async def process_convertion_result(self):
        if self.convertion_queue.empty():
            return

        while not self.convertion_queue.empty():
            try:
                future_result = await self.convertion_queue.get()
                while not future_result.done():
                    await asyncio.sleep(0.001)
                video = future_result.result()
                if not video:
                    return
                output_filename = (
                    f"{video.args[3].split('.')[0]}.tar.{self.settings['TAR_TYPE']}"
                )
                logger.debug("Prepare file 1")
                video_file = pathlib.Path(video.args[3])
                new_path = pathlib.Path(video.args[3].replace("/_", "/"))
                logger.debug("Prepare file 2")

                video_file.rename(new_path)
                video.args[2].unlink()
                logger.debug("Prepare file 3")

                result = self.loop.run_in_executor(
                    self.compression_pool, self.compress, output_filename, new_path
                )
                if not self.compression_queue.full():
                    await self.compression_queue.put(result)
                else:
                    return
            except Exception as e:
                logger.exception(e)
