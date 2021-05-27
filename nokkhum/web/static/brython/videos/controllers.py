from browser import document, ajax, timer, html

import javascript as js


class VideoController:
    def __init__(self, get_video_url=""):
        self.get_video_url = get_video_url
        self.wait_video_timer = None

    def check_video_response(self, req):
        print(req.text)

    def video_finder(self):
        ajax.get(self.get_video_url, oncomplete=self.check_video_response)

    def render_video(self, ev):
        print("Play video")
        document["video-player"].unbind()
        ev.target.className = "notched huge circle loading icon"
        self.wait_video_timer = timer.set_interval(self.video_finder, 1000)

    def start(self):
        document["video-player"].bind("click", self.render_video)
        print("Run")