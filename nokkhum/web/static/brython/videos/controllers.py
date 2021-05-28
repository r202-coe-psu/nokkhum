from browser import document, ajax, timer, html

import javascript as js


class VideoController:
    def __init__(self, get_video_url="", video_path=""):
        self.get_video_url = get_video_url
        self.wait_video_timer = None
        self.video_path = video_path
        self.wait_btn_timer = None

    def insert_video_source(self):
        document["video-player"].clear()
        video_element = html.VIDEO(
            "",
            style={"width": "100%"},
            src=self.video_path,
            autoplay=True,
            controls=True,
        )
        document["video-player"] <= video_element

    def check_video_response(self, req):
        # print(req.status)
        if req.status != 200:
            return
        timer.clear_interval(self.wait_video_timer)
        self.insert_video_source()

    def video_finder(self):
        ajax.get(self.get_video_url, oncomplete=self.check_video_response)

    def render_video(self, ev):
        print("Play video")
        document["video-player"].unbind()
        document["video-play-icon"].className = "notched huge circle loading icon"
        self.video_finder()
        self.wait_video_timer = timer.set_interval(self.video_finder, 5000)

    def update_download_btn(self, req):
        if req.status != 200:
            print("not foundd")
            return
        print("foundd")
        timer.clear_interval(self.wait_btn_timer)
        # print(document["download-mp4"].__dict__)
        document["download-mp4"].href = self.video_path
        document["download-mp4"].className = "ui primary button"
        document["download-mp4"].click()

    def prepare_btn_for_download(self):
        ajax.get(self.get_video_url, oncomplete=self.update_download_btn)

    def check_download_btn(self, ev):
        ev.target.className = "ui loading button"
        document["download-mp4"].unbind()

        self.prepare_btn_for_download()
        self.wait_btn_timer = timer.set_interval(self.prepare_btn_for_download, 5000)

    def start(self):
        document["video-player"].bind("click", self.render_video)
        document["download-mp4"].bind("click", self.check_download_btn)
        print("Run")
