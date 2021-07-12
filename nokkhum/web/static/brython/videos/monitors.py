from browser import document, ajax, timer, html

import javascript as js


class VideoMonitor:
    def __init__(self, get_video_url="", streaming_url="", static_url=""):
        self.streaming_url = streaming_url
        self.get_video_url = get_video_url
        self.video_path = ""
        self.wait_video_timer = None
        self.static_url = static_url

    def switch_live(self, ev):
        monitor = document["monitor"]
        monitor.clear()
        monitor <= html.IMG(src=self.streaming_url, width="100%")

    def insert_video_source(self):
        # document["video-player"].clear()
        video_element = html.VIDEO(
            "",
            style={"width": "100%"},
            src=f"{self.static_url}{self.video_path}.mp4",
            autoplay=True,
            controls=True,
        )
        document["monitor"].clear()
        document["monitor"] <= video_element
        print("insert")
        self.video_path = ""

    def check_video_response(self, req):
        # print(req.status)
        if req.status != 200:
            return
        timer.clear_interval(self.wait_video_timer)
        self.insert_video_source()

    def video_finder(self):
        if not self.video_path:
            return
        ajax.get(
            f"{self.get_video_url}/{self.video_path}",
            oncomplete=self.check_video_response,
        )

    def render_video(self, ev):
        print("Play video")
        document["monitor"].unbind()
        document["video-play-icon"].className = "notched huge circle loading icon"
        self.video_finder()
        self.wait_video_timer = timer.set_interval(self.video_finder, 5000)

    def switch_view_video(self, ev):
        if not ev.target.parent.id:
            video_id = ev.target.parent.parent.id
        else:
            video_id = ev.target.parent.id
        print(video_id)
        if "motion" in video_id:
            _, processor_id, date, time, milli_sec, _, _ = video_id.split("-")
        else:
            _, processor_id, date, time, milli_sec = video_id.split("-")
        self.video_path = f"{processor_id}/{date}/{video_id.replace('video-', '')}"
        print(self.video_path)
        document["monitor"].bind("click", self.render_video)

    def start(self):
        print("start")
        document["view-live"].bind("click", self.switch_live)
        document["monitor"].bind("click", self.render_video)
        view_video_elems = document.select(".view-video")
        for elem in view_video_elems:
            elem.bind("click", self.switch_view_video)
