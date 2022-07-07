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
import datetime
import pprint
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VideoProcessStatus:
    name: str
    status: str = "no operation"
    created_date: datetime.datetime = datetime.datetime.now()
    updated_date: datetime.datetime = datetime.datetime.now()
    message: str = ""


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
        self.compression_queue = asyncio.queues.Queue(maxsize=20)
        self.convertion_queue = asyncio.queues.Queue(maxsize=20)

        self.video_process_status = dict()

    def compress(self, output_filename, video):

        key = video.stem
        self.video_process_status[key].status = "compression"
        self.video_process_status[key].updated_date = datetime.datetime.now()
        if not video.exists():
            return

        with tarfile.open(output_filename, f"w:{self.settings['TAR_TYPE']}") as tar:
            tar.add(video, arcname=os.path.basename(video))

        video.unlink()
        self.video_process_status[key].status = "compression success"
        self.video_process_status[key].updated_date = datetime.datetime.now()
        return output_filename

    async def process_compression_result(self):
        if self.compression_queue.empty():
            return

        while not self.compression_queue.empty():
            future_result = await self.compression_queue.get()
            while not future_result.done():
                await asyncio.sleep(0.001)

            result = future_result.result()
            if not result:
                continue

            tar_file = result
            # logger.debug(tar_file)
            # video_mp4 = result[1]
            tar_path = pathlib.Path(tar_file)

            key = tar_path.stem.replace("_", "")
            if "." in key:
                p = pathlib.Path(key)
                key = p.stem

            if key not in self.video_process_status:
                logger.debug(f"key -> {key} not found")
                continue

            self.video_process_status[key].status = "transfer file"
            self.video_process_status[key].updated_date = datetime.datetime.now()
            # tar_path.rename(
            #     pathlib.Path(
            #         tar_file.replace("/_", "/").replace(
            #             self.settings["NOKKHUM_PROCESSOR_RECORDER_CACHE_PATH"],
            #             self.settings["NOKKHUM_PROCESSOR_RECORDER_PATH"],
            #         )
            #     )
            # )
            # logger.debug(str(tar_file).replace("_", "/"))
            if not tar_path.exists():
                continue

            new_tar_path = pathlib.Path(
                str(tar_file)
                .replace("/_", "/")
                .replace(
                    self.settings["NOKKHUM_PROCESSOR_RECORDER_CACHE_PATH"],
                    self.settings["NOKKHUM_PROCESSOR_RECORDER_PATH"],
                )
            )
            if not new_tar_path.parent.exists():
                new_tar_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy(tar_path, new_tar_path)
            tar_path.unlink()

            self.video_process_status.pop(key)
            # video_mp4.unlink()

    def check_file_log(self, date_dir):
        for log in date_dir.iterdir():
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

    async def remove_empty_video_records_cache(self):
        for processor_dir in self.cache_path.iterdir():
            for date_dir in processor_dir.iterdir():
                if date_dir.name == "log":
                    self.check_file_log(date_dir)
                    continue

                year = int(date_dir.name[0:4])
                month = int(date_dir.name[4:6])
                day = int(date_dir.name[6:8])
                expired_date = datetime.date.today() - datetime.timedelta(
                    days=self.settings[
                        "NOKKHUM_PROCESSOR_RECORDER_CACHE_PATH_EXPIRED_DAYS"
                    ]
                )
                expired_date = datetime.datetime.combine(
                    expired_date, datetime.time(0, 0, 0)
                )
                if datetime.datetime(year, month, day) > expired_date:
                    continue

                for video_file in date_dir.iterdir():
                    video_file.unlink()
                # if date_dir.iterdir():
                #     logger.debug("have file continue")
                #     continue
                # logger.debug(date_dir.name)
                date_dir.rmdir()

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
        logger.debug("monitor mkv file")
        logger.debug(f"waiting {len(self.video_process_status)}")
        pprint.pprint(self.video_process_status)
        # try:
        for processor_dir in self.cache_path.iterdir():
            for date_dir in processor_dir.iterdir():
                if not (date_dir.name).isdigit():
                    continue

                for video in date_dir.iterdir():
                    if (
                        date_dir / f"{video.stem}.mp4"
                    ).exists() and "_" not in video.name:

                        if video.name[0] != "_":
                            output_filename = (
                                date_dir
                                / f"_{video.name.split('.')[0]}.tar.{self.settings['TAR_TYPE']}"
                            )

                            key = video.stem

                            if key in self.video_process_status:
                                continue

                            self.video_process_status[key] = VideoProcessStatus(
                                name=video.stem,
                                status="waiting compression",
                                message="recover",
                            )

                            result = self.loop.run_in_executor(
                                self.compression_pool,
                                self.compress,
                                output_filename,
                                video,
                            )
                            if not self.compression_queue.full():
                                await self.compression_queue.put(result)
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
                        shutil.copy(video, new_image_path)
                        video.unlink()

                    if video.suffix != ".mkv":
                        continue

                    if video.name[0] == "_":
                        self.check_video_file_name(video)
                        continue

                    if video.stem in self.video_process_status:
                        continue

                    self.video_process_status[video.stem] = VideoProcessStatus(
                        name=video.stem, status="wait convertion"
                    )

                    result = self.loop.run_in_executor(
                        self.convertion_pool, self.convert, video
                    )

                    logger.debug(f"wait convertion_queue {video}")
                    while self.convertion_queue.full():
                        await asyncio.sleep(0.001)

                    await self.convertion_queue.put(result)
        # except Exception as e:
        #     logger.exception(e)

    def convert(self, video):
        self.video_process_status[video.stem].status = "converting"
        self.video_process_status[video.stem].updated_date = datetime.datetime.now()

        if not video.exists():
            return

        name = video.name.split(".")[0]
        logger.debug(f"converting >> {video.name}")
        with_mp4 = str(video.parents[0]) + "/_" + name + ".mp4"
        mp4_path = pathlib.Path(with_mp4.replace("/_", "/"))

        if mp4_path.exists():
            return

        result = (
            ffmpeg.input(video)
            .output(with_mp4)
            .run_async(overwrite_output=True, quiet=True)
        )
        # logger.debug("waiting")

        result.wait()

        self.video_process_status[video.stem].status = "convert success"
        self.video_process_status[video.stem].updated_date = datetime.datetime.now()
        logger.debug(f"end convert >> {video.name}")
        return result

    async def process_convertion_result(self):
        if self.convertion_queue.empty():
            return

        while not self.convertion_queue.empty():
            future_result = await self.convertion_queue.get()
            while not future_result.done():
                await asyncio.sleep(0.001)

            video = future_result.result()
            if not video:
                logger.debug(f"got {video}")
                self.video_process_status.pop(video.stem)
                continue

            output_filename = (
                f"{video.args[3].split('.')[0]}.tar.{self.settings['TAR_TYPE']}"
            )

            video_file = pathlib.Path(video.args[3])
            new_path = pathlib.Path(video.args[3].replace("/_", "/"))

            if not video_file.exists():
                logger.debug(f"compress {video_file} not exists")
                self.video_process_status.pop(new_path.stem)
                continue

            video_file.rename(new_path)
            video.args[2].unlink()
            video.terminate()

            self.video_process_status[new_path.stem].status = "wait compression"
            self.video_process_status[
                new_path.stem
            ].updated_date = datetime.datetime.now()
            result = self.loop.run_in_executor(
                self.compression_pool, self.compress, output_filename, new_path
            )

            while self.compression_queue.full():
                await asyncio.sleep(0.001)

            await self.compression_queue.put(result)

    async def clear_cache_dir(self):
        logger.debug("begin clear cache dir")

        for f in self.cache_path.glob("**/*"):
            if not f.is_file():
                continue

            if f.name[0] == "_" and f.suffix == ".mkv":
                logger.debug(f"rename file: {f.name}")
                f.rename(f.parent / f.name[1:])
            elif f.name[0] == "_":
                logger.debug(f"remove file: {f.name}")
                f.unlink()

        for d in self.cache_path.glob("*/*"):
            if not d.is_dir():
                continue

            if len(list(d.iterdir())) == 0:
                logger.debug(f"remove dir: {d.name}")
                d.rmdir()

        logger.debug("end clear cache dir")
