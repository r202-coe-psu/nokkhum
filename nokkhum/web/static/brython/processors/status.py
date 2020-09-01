from browser import ajax, document, window, timer, html, bind
import javascript


class ProcessorStatus:
    def __init__(self, url, icon_size="large"):
        self.icon_size = icon_size
        self.get_state_url = url

    def disable_button(self, docs, cam_id):
        for doc in docs:
            if doc.id == cam_id:
                doc.disabled = True

    def enable_button(self, docs, cam_id):
        for doc in docs:
            if doc.id == cam_id:
                doc.disabled = False

    @bind("button.stoplpr", "click")
    def stop_lpr(ev):
        # print(ev.target.id)
        camera_id, project_id = (ev.target.id).split("/")
        ajax.post(f"/cameras/{camera_id}/stoplpr", data={"project_id": project_id})

    @bind("button.startlpr", "click")
    def start_lpr(ev):
        # print('start', ev.target.id)
        camera_id, project_id = (ev.target.id).split("/")
        ajax.post(f"/cameras/{camera_id}/startlpr", data={"project_id": project_id})

    def update_state(self, req_data):
        for data in req_data:
            print(data)
            # document[f"state-{data['camera_id']}"].text = data['state']
            data_id = data["camera_id"] + "/" + data["project_id"]
            i = html.I()
            color = "grey"
            if data["state"] in ["running", "start"]:
                color = "green"
                s = html.SPAN(style={"color": "green"})
                self.disable_button(document.select(".startlpr"), data_id)
                self.enable_button(document.select(".stoplpr"), data_id)
            elif data["state"] in ["starting"]:
                color = "yellow"
                s = html.SPAN(style={"color": "yellow"})
                self.disable_button(document.select(".stoplpr"), data_id)
                self.enable_button(document.select(".startlpr"), data_id)
            elif data["state"] in ["stop"]:
                color = "grey"
                s = html.SPAN(style={"color": "grey"})
                self.disable_button(document.select(".stoplpr"), data_id)
                self.enable_button(document.select(".startlpr"), data_id)
            elif data["state"] in ["stopping"]:
                color = "red"
                s = html.SPAN(style={"color": "red"})
                self.disable_button(document.select(".stoplpr"), data_id)
                self.enable_button(document.select(".startlpr"), data_id)

            i.class_name = f"ui {color} circle icon {self.icon_size}"
            try:
                document[f"state-{data['camera_id']}"].text = ""
                document[f"state-{data['camera_id']}"] <= i + s
            except Exception:
                continue

    def on_ajax_complete(self, request):
        request_data = javascript.JSON.parse(request.text)
        # print(request_data)
        self.update_state(request_data)

    def get_all_camera_state(self):
        ajax.get(
            f"{self.get_state_url}", oncomplete=self.on_ajax_complete,
        )

    def start(self):
        self.get_all_camera_state()
        timer.set_interval(self.get_all_camera_state, 5000)
