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
        self.cache_path = pathlib.Path(self.settings["NOKKHUM_PROCESSOR_RECORDER_CACHE_PATH"])
        self.recorder_path = pathlib.Path(self.settings["NOKKHUM_PROCESSOR_RECORDER_PATH"])
        self.loop = asyncio.get_event_loop()
        self.compression_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=settings.get("NOKKHUM_COMPUTE_COMPRESSION_MAX_WORKER")
        )
        self.convertion_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=settings.get("NOKKHUM_COMPUTE_CONVERTION_MAX_WORKER")
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
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).date() >= log_date.date():
                log.unlink()

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
                    if dir_file.name == "log":
                        self.check_file_log(dir_file)
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

    async def remove_mp4_file(self):
        logger.debug("start remove mp4")
        for processor_dir in self.path.iterdir():
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
        # try:
        #     logger.debug("converting")
        #     name = video.name.split(".")[0]
        #     with_mp4 = str(video.parents[0]) + name + ".mp4"
        #     result = ffmpeg.input(video).output(with_mp4).run_async(overwrite_output=True)
        #     logger.debug("waiting")
        #     result.wait()
        #     logger.debug("compressing")
        with tarfile.open(output_filename, f"w:{self.settings['TAR_TYPE']}") as tar:
            tar.add(video, arcname=os.path.basename(video))
            return output_filename
        # except Exception as e:
        #     logger.exception(e)

    async def process_compression_result(self):
        if self.compression_queue.empty():
            # await asyncio.sleep(0.1)
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
            # logger.debug(f"remove video {video}")
            # video.unlink()
            except Exception as e:
                logger.exception(e)

    async def extract_tar_file(self, data):
        mp4_path = (
            self.path
            / data["processor_id"]
            / data["date_dir"]
            / f'{data["filename"]}.mp4'
        )
        # logger.debug(f"{mp4_path}>>>>>{mp4_path.exists()}")

        if mp4_path.exists():
            return

        try:
            source_file = (
                self.path
                / data["processor_id"]
                / data["date_dir"]
                / f"{data['filename']}.tar.{self.settings['TAR_TYPE']}"
            )
            tar = tarfile.open(source_file, f"r:{self.settings['TAR_TYPE']}")
            tar.extractall(path=source_file.parents[0])
            tar.close()
        except Exception as e:
            logger.exception(e)

    # async def compress_video_files(self):
    #     logger.debug("start compress file mp4")
    #     for processor_dir in self.path.iterdir():
    #         for date_dir in processor_dir.iterdir():
    #             if not (date_dir.name).isdigit():
    #                 continue
    #             for video in date_dir.iterdir():
    #                 if video.suffix != ".mp4":
    #                     continue
    #                 if video.name[0] == "_":
    #                     continue
    #                 # logger.debug(video)
    #                 output_filename = f'{date_dir/pathlib.Path(video.name.split(".")[0])}.tar.{self.settings["TAR_TYPE"]}'
    #                 result = self.loop.run_in_executor(
    #                     self.compression_pool, self.compress, output_filename, video
    #                 )
    #                 if not self.compression_queue.full():
    #                     await self.compression_queue.put(result)
    #                 else:
    #                     return

    def check_video_file_name(self, video):
        filename = video.parents[0] / video.name[1:]
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
        for processor_dir in self.path.iterdir():
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
                    # if not video.name in data:
                    #     data[video.name] = 0
                    # data[video.name] += 1
                    # output_filename = f'{date_dir/pathlib.Path(video.name.split(".")[0])}.tar.{self.settings["TAR_TYPE"]}'
                    # logger.debug(f"dataaaaaaaaaaa {data}")
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
            # logger.debug(f">>>>>>> {with_mp4}")
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
            # await asyncio.sleep(0.1)
            return

        while not self.convertion_queue.empty():
            future_result = await self.convertion_queue.get()
            # try:
            while not future_result.done():
                await asyncio.sleep(0.001)
            video = future_result.result()
            if not video:
                return
            # logger.debug(f">>>>>>>>>>> {video.__dict__}")
            # except Exception as e:
            #     logger.exception(e)
            # video_file_path = pathlib.Path()
            output_filename = (
                f"{video.args[3].split('.')[0]}.tar.{self.settings['TAR_TYPE']}"
            )
            # output_filename = f'{date_dir/pathlib.Path(video.name.split(".")[0])}.tar.{self.settings["TAR_TYPE"]}'
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
