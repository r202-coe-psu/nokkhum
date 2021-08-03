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
        # self.recorder_path = pathlib.Path(self.settings["NOKKHUM_PROCESSOR_RECORDER_PATH"])
        self.cache_path = pathlib.Path(
            self.settings["NOKKHUM_PROCESSOR_RECORDER_CACHE_PATH"]
        )
        self.recorder_path = pathlib.Path(
            self.settings["NOKKHUM_PROCESSOR_RECORDER_PATH"]
        )
        self.loop = asyncio.get_event_loop()
        self.compression_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=settings.get("NOKKHUM_CONTROLLER_COMPRESSION_MAX_WORKER")
        )
        self.convertion_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=settings.get("NOKKHUM_CONTROLLER_CONVERTION_MAX_WORKER")
        )
        self.compression_queue = asyncio.queues.Queue(maxsize=100)
        self.convertion_queue = asyncio.queues.Queue(maxsize=100)

    def check_file_log(self, dir_file):
        for log in dir_file.iterdir():
            if len(log.name.split(".")) < 3:
                continue
            date = log.name.split(".")[-1]
            log_date = datetime.datetime.strptime(date, "%Y-%m-%d")
            if (
                datetime.datetime.now()
                - datetime.timedelta(
                    days=self.settings["NOKKHUM_PROCESSOR_RECORDER_LOGS_EXPIRED_DAYS"]
                )
            ).date() >= log_date.date():
                log.unlink()

    def check_expired_dir(self, files_path, storage_period):

        if storage_period == 0:
            return
        expired_date = datetime.date.today() - datetime.timedelta(days=storage_period)
        expired_date = datetime.datetime.combine(expired_date, datetime.time(0, 0, 0))

        for dir_file in files_path.iterdir():
            if not dir_file.name.isdigit():
                if dir_file.name == "log":
                    self.check_file_log(dir_file)
                continue

            year = int(dir_file.name[0:4])
            month = int(dir_file.name[4:6])
            day = int(dir_file.name[6:8])

            if datetime.datetime(year, month, day) > expired_date:
                continue

            # logger.debug('expired')
            images_path = files_path / dir_file
            for video_file in images_path.iterdir():
                video_file.unlink()

            dir_file.rmdir()

    async def remove_expired_video_records(self):
        logger.debug("start remove expired records")

        processors = models.Processor.objects()
        for processor in processors:
            # files_cache_path = self.cache_path / str(processor.id)
            # if files_cache_path.exists() and files_cache_path.is_dir():
            #     self.check_expired_dir(
            #         files_cache_path,
            #         self.settings["NOKKHUM_PROCESSOR_RECORDER_CACHE_PATH_EXPIRED_DAYS"],
            #     )

            storage_period = processor.storage_period

            files_recorder_path = self.recorder_path / str(processor.id)
            if files_recorder_path.exists() and files_recorder_path.is_dir():
                self.check_expired_dir(files_recorder_path, storage_period)

    async def remove_web_log_file(self):
        logger.debug("start remove web log")
        log_path = self.recorder_path / "web" / "log"
        if not log_path.exists():
            return
        for log in self.recorder_path.iterdir():
            date = log.name.replace("uwsgi-", "")
            log_date = datetime.datetime.strptime(date, "%Y-%m-%d")
            if (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).date() >= log_date.date():
                log.unlink()

    async def remove_mp4_file(self):
        logger.debug("start remove mp4")
        for processor_dir in self.recorder_path.iterdir():
            for date_dir in processor_dir.iterdir():
                if not (date_dir.name).isdigit():
                    continue
                for video in date_dir.iterdir():
                    if video.suffix != ".mp4":
                        continue
                    if video.name[0] == "_":
                        continue
                    tar_file = (
                        video.parents[0]
                        / f"_{video.stem}.tar.{self.settings['TAR_TYPE']}"
                    )

                    if not tar_file.exists():
                        video.unlink()
                        continue

                    last_update = datetime.datetime.fromtimestamp(
                        tar_file.stat().st_mtime
                    )
                    if (datetime.datetime.now() - last_update).seconds > 3600:

                        result = self.loop.run_in_executor(
                            self.compression_pool, self.compress, tar_file, video
                        )
                        if not self.compression_queue.full():
                            await self.compression_queue.put(result)
                        else:
                            continue
        logger.debug("remove mp4 finish")

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
                tar_path.rename(pathlib.Path(tar_file.replace("/_", "/")))
            except Exception as e:
                logger.exception(e)

    async def extract_tar_file(self, data):
        mp4_path = (
            self.recorder_path
            / data["processor_id"]
            / data["date_dir"]
            / f'{data["filename"]}.mp4'
        )

        if mp4_path.exists():
            return

        try:
            source_file = (
                self.recorder_path
                / data["processor_id"]
                / data["date_dir"]
                / f"{data['filename']}.tar.{self.settings['TAR_TYPE']}"
            )
            tar = tarfile.open(source_file, f"r:{self.settings['TAR_TYPE']}")
            tar.extractall(path=source_file.parents[0])
            tar.close()
        except Exception as e:
            logger.exception(e)

    def check_video_file_name(self, video):
        filename = video.parents[0] / video.name[1:]
        if "motion" in video.name:
            _, date, time, _, _, _ = video.name.split("-")
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
        for processor_dir in self.recorder_path.iterdir():
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
            future_result = await self.convertion_queue.get()
            while not future_result.done():
                await asyncio.sleep(0.001)
            video = future_result.result()
            if not video:
                return
            output_filename = (
                f"{video.args[3].split('.')[0]}.tar.{self.settings['TAR_TYPE']}"
            )
            video_file = pathlib.Path(video.args[3])
            new_path = pathlib.Path(video.args[3].replace("/_", "/"))
            video_file.rename(new_path)
            video.args[2].unlink()
            result = self.loop.run_in_executor(
                self.compression_pool, self.compress, output_filename, new_path
            )
            if not self.compression_queue.full():
                await self.compression_queue.put(result)
            else:
                return
