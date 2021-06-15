from nokkhum import models
import datetime

import asyncio
import logging
import pathlib
import tarfile
import os
import shutil
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
            return [output_filename, video]

    async def process_compression_result(self):
        if self.compression_queue.empty():
            return

        while not self.compression_queue.empty():
            future_result = await self.compression_queue.get()
            while not future_result.done():
                await asyncio.sleep(0.001)
            try:
                result = future_result.result()
                tar_file = result[0]
                # logger.debug(tar_file)
                video_mp4 = result[1]
                tar_path = pathlib.Path(tar_file)
                # tar_path.rename(
                #     pathlib.Path(
                #         tar_file.replace("/_", "/").replace(
                #             self.settings["NOKKHUM_PROCESSOR_RECORDER_CACHE_PATH"],
                #             self.settings["NOKKHUM_PROCESSOR_RECORDER_PATH"],
                #         )
                #     )
                # )
                new_tar_path = pathlib.Path(
                        tar_file.replace("/_", "/").replace(
                            self.settings["NOKKHUM_PROCESSOR_RECORDER_CACHE_PATH"],
                            self.settings["NOKKHUM_PROCESSOR_RECORDER_PATH"],
                        )
                    )
                if not new_tar_path.parent.exists():
                     new_tar_path.parent.mkdir(parents=True, exist_ok=True)

                shutil.move(tar_path, new_tar_path)

                video_mp4.unlink()
            except Exception as e:
                logger.exception(e)

    def check_file_log(self, date_dir):
        for log in date_dir.iterdir():
            if len(log.name.split(".")) < 3:
                continue
            date = log.name.split(".")[-1]
            log_date = datetime.datetime.strptime(date, "%Y-%m-%d")
            if (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).date() >= log_date.date():
                log.unlink()

    async def remove_empty_video_records_cache(self):
        for processor_dir in self.cache_path.iterdir():
            for date_dir in processor_dir.iterdir():
                if date_dir.name == "log":
                    self.check_file_log(date_dir)
                    continue

                year = int(date_dir.name[0:4])
                month = int(date_dir.name[4:6])
                day = int(date_dir.name[6:8])
                expired_date = datetime.date.today() - datetime.timedelta(days=2)
                expired_date = datetime.datetime.combine(
                    expired_date, datetime.time(0, 0, 0)
                )
                if datetime.datetime(year, month, day) > expired_date:
                    continue
                # if date_dir.iterdir():
                #     logger.debug("have file continue")
                #     continue
                # logger.debug(date_dir.name)
                date_dir.rmdir()

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
        # try:
        for processor_dir in self.cache_path.iterdir():
            for date_dir in processor_dir.iterdir():
                if not (date_dir.name).isdigit():
                    continue
                for video in date_dir.iterdir():
                    if (date_dir / f"{video.name.split('.')[0]}.mp4").exists():
                        continue
                    if video.suffix == ".png":
                        new_image_path = (
                            self.recorder_path
                            / processor_dir.stem
                            / date_dir.stem
                            / video.name
                        )
                        if new_image_path.exists():
                            continue
                        if not new_image_path.parent.exists():
                            new_image_path.parent.mkdir(parents=True)
                        # video.rename(new_image_path)
                        shutil.move(video, new_image_path)

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
        # except Exception as e:
        #     logger.exception(e)

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
            except Exception as e:
                logger.exception(e)
